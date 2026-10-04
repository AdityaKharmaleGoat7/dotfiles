# Run with pwsh -NoProfile -File tests/ai.ps1. No AI service calls are made.
$ErrorActionPreference = 'Stop'
$repoDirectory = Split-Path -Parent $PSScriptRoot
$testDirectory = Join-Path ([IO.Path]::GetTempPath()) ('ai-tests.' + [guid]::NewGuid().ToString('N'))
$originalLocation = Get-Location
$savedEnvironment = @{}
foreach ($name in @('AI_TEST_RECORD', 'AI_TEST_CONTEXT', 'AI_TEST_EXIT', 'GIT_CONFIG_GLOBAL', 'GIT_CONFIG_NOSYSTEM', 'OPENCODE_CONFIG_CONTENT')) {
    $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name)
}
$script:availableBackends = @('codex', 'claude', 'opencode')
$script:passed = 0

function Assert-Contains($Path, $Text) {
    if (!(Get-Content -LiteralPath $Path -Raw).Contains($Text)) {
        throw "Expected '$Text' in $Path"
    }
}

function Invoke-Case([int]$Expected, [string[]]$Arguments) {
    ai @Arguments 2> (Join-Path $testDirectory 'error.txt') | Out-Null
    if ($LASTEXITCODE -ne $Expected) {
        throw "ai $Arguments`: expected $Expected, got $LASTEXITCODE"
    }
    $script:passed++
}

function Invoke-TestGit([string[]]$Arguments) {
    & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git fixture command failed: $Arguments" }
}

try {
    New-Item -ItemType Directory -Path $testDirectory | Out-Null
    $binDirectory = Join-Path $testDirectory 'bin'
    New-Item -ItemType Directory -Path $binDirectory | Out-Null
    $env:AI_TEST_RECORD = Join-Path $testDirectory 'record.txt'
    $env:AI_TEST_CONTEXT = Join-Path $testDirectory 'context.md'
    $env:AI_TEST_EXIT = '0'
    $env:GIT_CONFIG_GLOBAL = Join-Path $testDirectory 'gitconfig'
    $env:GIT_CONFIG_NOSYSTEM = '1'
    Set-Content -LiteralPath $env:GIT_CONFIG_GLOBAL -Value ''
    $fakeCli = @'
$name = [IO.Path]::GetFileNameWithoutExtension($PSCommandPath)
$record = @($name, (Get-Location).Path) + $args
[IO.File]::WriteAllLines($env:AI_TEST_RECORD, [string[]]$record)
[IO.File]::WriteAllText(($env:AI_TEST_RECORD + '.env'), [string]$env:OPENCODE_CONFIG_CONTENT)
$prompt = [string]$args[-1]
$prefix = 'Read the study instructions and context in '
$suffix = ', then begin the requested study. Stay read-only for the entire conversation.'
$context = $prompt.Substring($prefix.Length, $prompt.Length - $prefix.Length - $suffix.Length)
[IO.File]::WriteAllText(($env:AI_TEST_RECORD + '.path'), $context)
Copy-Item -LiteralPath $context -Destination $env:AI_TEST_CONTEXT
$global:LASTEXITCODE = [int]$env:AI_TEST_EXIT
'@
    foreach ($name in @('codex', 'claude', 'opencode')) {
        Set-Content -LiteralPath (Join-Path $binDirectory "$name.ps1") -Value $fakeCli
    }
    # Limit CLI discovery to these fake scripts, even on a configured host.
    function Get-Command {
        [CmdletBinding()]
        param([string]$Name, [object]$CommandType)
        if ($Name -in @('codex', 'claude', 'opencode')) {
            if ($Name -in $script:availableBackends) {
                [pscustomobject]@{ Source = Join-Path $binDirectory "$Name.ps1" }
            }
        }
        else {
            Microsoft.PowerShell.Core\Get-Command @PSBoundParameters
        }
    }
    $helperDirectory = Join-Path $testDirectory 'study config'
    Copy-Item -LiteralPath (Join-Path $repoDirectory 'config/ai') -Destination $helperDirectory -Recurse
    . (Join-Path $helperDirectory 'ai.ps1')
    $fixture = Join-Path $testDirectory 'repo'
    $nested = Join-Path $fixture 'nested'
    New-Item -ItemType Directory -Path $nested -Force | Out-Null
    Set-Location -LiteralPath $fixture
    Invoke-TestGit -Arguments @('init', '-q')
    Set-Content -LiteralPath 'file with spaces.txt' -Value 'old behavior'
    Invoke-TestGit -Arguments @('add', '--', 'file with spaces.txt')
    Invoke-TestGit -Arguments @('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'baseline')
    Set-Location -LiteralPath $nested
    # Expected validation errors should be recorded rather than terminating tests.
    $ErrorActionPreference = 'Continue'
    Invoke-Case -Expected 0 -Arguments @('--help')
    Invoke-Case -Expected 0 -Arguments @()
    foreach ($mode in @('study', 'architecture')) {
        Invoke-Case -Expected 0 -Arguments @($mode)
        Assert-Contains $env:AI_TEST_CONTEXT (Get-Content -LiteralPath (Join-Path $helperDirectory "prompts/$mode.md") -Raw)
        Assert-Contains $env:AI_TEST_CONTEXT 'Do not modify code'
        Assert-Contains $env:AI_TEST_CONTEXT 'ASD-STE100'
    }
    foreach ($mode in @('explain', 'why', 'quiz')) {
        Invoke-Case -Expected 0 -Arguments @($mode, '../file with spaces.txt')
        Assert-Contains $env:AI_TEST_CONTEXT ('Target (literal data): ' + (Join-Path $fixture 'file with spaces.txt'))
    }
    Invoke-Case -Expected 0 -Arguments @('explain', 'event', 'loop')
    Assert-Contains $env:AI_TEST_CONTEXT 'Target (literal data): event loop'
    Assert-Contains $env:AI_TEST_CONTEXT 'follow-up questions'
    Invoke-Case -Expected 0 -Arguments @('trace', 'run$(touch injected); --flag')
    Assert-Contains $env:AI_TEST_CONTEXT 'Target (literal data): run$(touch injected); --flag'
    Assert-Contains $env:AI_TEST_RECORD 'read-only'
    Assert-Contains $env:AI_TEST_RECORD 'never'
    if ((Get-Content $env:AI_TEST_RECORD)[0] -ne 'codex') { throw 'Codex preference failed' }
    if (Test-Path -LiteralPath (Get-Content ($env:AI_TEST_RECORD + '.path') -Raw)) { throw 'Context was not cleaned up' }
    if ((Get-Location).Path -ne $nested -or (Test-Path injected)) { throw 'Caller state changed' }
    Invoke-Case -Expected 2 -Arguments @('missing')
    Invoke-Case -Expected 2 -Arguments @('study', 'extra')
    Invoke-Case -Expected 2 -Arguments @('explain')
    Invoke-Case -Expected 2 -Arguments @('trace', 'one', 'two')
    Invoke-Case -Expected 2 -Arguments @('quiz', '')
    Invoke-Case -Expected 0 -Arguments @('explain', 'nonexistent')
    Assert-Contains $env:AI_TEST_CONTEXT 'Target (literal data): nonexistent'
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    if ((Get-Content $env:AI_TEST_CONTEXT -Raw).Contains('diff --git')) { throw 'Clean fixture has a diff' }
    Set-Content -LiteralPath '../file with spaces.txt' -Value 'staged behavior'
    Invoke-TestGit -Arguments @('add', '--', '../file with spaces.txt')
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT '+staged behavior'
    Set-Content -LiteralPath '../file with spaces.txt' -Value 'working behavior'
    Set-Content -LiteralPath '../untracked.txt' -Value 'untracked contents must not be read'
    $before = @(git status --porcelain; git diff; git diff --cached) -join "`n"
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT '+staged behavior'
    Assert-Contains $env:AI_TEST_CONTEXT '+working behavior'
    Assert-Contains $env:AI_TEST_CONTEXT '?? untracked.txt'
    if ((Get-Content $env:AI_TEST_CONTEXT -Raw).Contains('untracked contents must not be read')) { throw 'Read untracked contents' }
    $after = @(git status --porcelain; git diff; git diff --cached) -join "`n"
    if ($before -ne $after) { throw 'Study modified the repository' }
    Invoke-TestGit -Arguments @('restore', '--staged', '--', '../file with spaces.txt')
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT '+working behavior'
    $env:AI_TEST_EXIT = '23'
    Invoke-Case -Expected 23 -Arguments @('study')
    if (Test-Path -LiteralPath (Get-Content ($env:AI_TEST_RECORD + '.path') -Raw)) { throw 'Failed session left context behind' }
    $env:AI_TEST_EXIT = '0'
    $script:availableBackends = @('claude', 'opencode')
    Invoke-Case -Expected 0 -Arguments @('architecture')
    if ((Get-Content $env:AI_TEST_RECORD)[0] -ne 'claude') { throw 'Claude fallback failed' }
    Assert-Contains $env:AI_TEST_RECORD 'Read,Glob,Grep'
    Assert-Contains $env:AI_TEST_RECORD 'mcp__*'
    $script:availableBackends = @('opencode')
    $env:OPENCODE_CONFIG_CONTENT = 'original config'
    Invoke-Case -Expected 0 -Arguments @('study')
    if ((Get-Content $env:AI_TEST_RECORD)[0] -ne 'opencode') { throw 'OpenCode fallback failed' }
    $config = Get-Content ($env:AI_TEST_RECORD + '.env') -Raw | ConvertFrom-Json
    if ($config.agent.'ai-study'.permission.bash -ne 'deny' -or $config.agent.'ai-study'.permission.edit -ne 'deny') { throw 'OpenCode write tools enabled' }
    if ($env:OPENCODE_CONFIG_CONTENT -ne 'original config') { throw 'OpenCode environment changed' }
    $script:availableBackends = @()
    Invoke-Case -Expected 127 -Arguments @('study')
    Set-Location -LiteralPath $testDirectory
    Invoke-Case -Expected 0 -Arguments @('--help')
    Invoke-Case -Expected 1 -Arguments @('study')
    $script:availableBackends = @('codex')
    $newRepo = Join-Path $testDirectory 'new-repo'
    New-Item -ItemType Directory -Path $newRepo | Out-Null
    Set-Location -LiteralPath $newRepo
    Invoke-TestGit -Arguments @('init', '-q')
    Set-Content -LiteralPath 'first.txt' -Value 'first file'
    Invoke-TestGit -Arguments @('add', '--', 'first.txt')
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT '+first file'
    [IO.File]::WriteAllBytes((Join-Path $newRepo 'binary.dat'), [byte[]]@(0, 1, 2, 3))
    Invoke-TestGit -Arguments @('add', '--', 'binary.dat')
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT 'Binary files'
    $largeFile = Join-Path $newRepo 'large.txt'
    [IO.File]::WriteAllLines($largeFile, [string[]](0..11999 | ForEach-Object { "large diff line $_" }))
    Invoke-TestGit -Arguments @('add', '--', 'large.txt')
    Invoke-Case -Expected 0 -Arguments @('diff-study')
    Assert-Contains $env:AI_TEST_CONTEXT '+large diff line 11999'
    if ((Get-Content $env:AI_TEST_RECORD -Raw).Length -ge 4096) { throw 'Diff was passed as a CLI argument' }

    $isolatedHome = Join-Path $testDirectory 'home'
    New-Item -ItemType Directory -Path $isolatedHome | Out-Null
    $profilePath = (Join-Path $repoDirectory 'config/powershell/profile.ps1').Replace("'", "''")
    $processInfo = [Diagnostics.ProcessStartInfo]::new()
    $processInfo.FileName = (Get-Process -Id $PID).Path
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.Environment['HOME'] = $isolatedHome
    $processInfo.Environment['USERPROFILE'] = $isolatedHome
    $processInfo.Environment['PATH'] = $binDirectory
    $processInfo.ArgumentList.Add('-NoProfile')
    $processInfo.ArgumentList.Add('-Command')
    $processInfo.ArgumentList.Add(". '$profilePath'; ai --help")
    $process = [Diagnostics.Process]::Start($processInfo)
    $profileOutput = $process.StandardOutput.ReadToEnd()
    $profileError = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0 -or !$profileOutput.Contains('Usage: ai') -or $profileError) {
        throw "Profile integration failed: $profileError"
    }
    $script:passed++
    $process.Dispose()
    Write-Output "PASS: $script:passed command cases; routing, arguments, diff snapshots, read-only flags, cleanup, and state preservation"
}
finally {
    Set-Location -LiteralPath $originalLocation.Path
    foreach ($name in $savedEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name])
    }
    Remove-Item -LiteralPath $testDirectory -Recurse -Force
}
