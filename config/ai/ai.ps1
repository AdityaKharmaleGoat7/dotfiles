# Sourced by the shared PowerShell profile.
$script:AiStudyDirectory = $PSScriptRoot

function global:ai {
    $studyArgs = @($args)
    $mode = if ($studyArgs.Count) { [string]$studyArgs[0] } else { '--help' }
    if ($mode -in @('--help', '-h')) {
        Write-Output 'Usage: ai study | architecture | explain <file-or-topic...> | trace <symbol>'
        Write-Output '          why <file-or-symbol> | diff-study | quiz <file-or-topic>'
        Write-Output 'Quote paths containing spaces. Explain topics can use multiple words.'
        Write-Output 'Opens an interactive, read-only study session; ask follow-up questions there.'
        Write-Output 'Backend preference: codex, claude, opencode (must be installed and authenticated).'
        Write-Output 'diff-study covers staged and unstaged tracked changes; untracked names only.'
        $global:LASTEXITCODE = 0
        return
    }
    $targetModes = @('explain', 'trace', 'why', 'quiz')
    if ($mode -notin @('study', 'architecture', 'diff-study') + $targetModes) {
        Write-Error "ai: unknown command: $mode; see ai --help" -ErrorAction Continue
        $global:LASTEXITCODE = 2
        return
    }
    $needsTarget = $mode -in $targetModes
    $expectedCount = if ($needsTarget) { 2 } else { 1 }
    $validCount = if ($mode -eq 'explain') { $studyArgs.Count -ge 2 } else { $studyArgs.Count -eq $expectedCount }
    $target = if ($needsTarget -and $studyArgs.Count -ge 2) { $studyArgs[1..($studyArgs.Count - 1)] -join ' ' } else { '' }
    if (!$validCount -or ($needsTarget -and [string]::IsNullOrWhiteSpace($target))) {
        Write-Error "ai: invalid arguments for $mode; quote spaces; see ai --help" -ErrorAction Continue
        $global:LASTEXITCODE = 2
        return
    }
    $callerDirectory = (Get-Location).Path
    $PSNativeCommandUseErrorActionPreference = $false
    if (!(Get-Command git -CommandType Application -ErrorAction SilentlyContinue)) {
        Write-Error 'ai: Git is required' -ErrorAction Continue
        $global:LASTEXITCODE = 1
        return
    }
    $repoRoot = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'ai: run this command inside a Git working tree' -ErrorAction Continue
        $global:LASTEXITCODE = 1
        return
    }
    if ($target -and (Test-Path -LiteralPath $target -PathType Leaf)) {
        $target = (Resolve-Path -LiteralPath $target).Path
    }
    $backend = $null
    foreach ($candidate in @('codex', 'claude', 'opencode')) {
        $backend = Get-Command $candidate -CommandType Application, ExternalScript -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($backend) { break }
    }
    if (!$backend) {
        Write-Error 'ai: install and authenticate Codex, Claude Code, or OpenCode first' -ErrorAction Continue
        $global:LASTEXITCODE = 127
        return
    }
    $contextDirectory = Join-Path ([IO.Path]::GetTempPath()) ('ai-study.' + [guid]::NewGuid().ToString('N'))
    $contextFile = Join-Path $contextDirectory 'context.md'
    $oldOpenCodeConfig = $env:OPENCODE_CONFIG_CONTENT
    $pushed = $false
    $result = 1
    try {
        $rules = Get-Content -LiteralPath (Join-Path $script:AiStudyDirectory 'rules/study.md') -Raw -ErrorAction Stop
        $prompt = Get-Content -LiteralPath (Join-Path $script:AiStudyDirectory "prompts/$mode.md") -Raw -ErrorAction Stop
        $context = "$rules`n$prompt`nRepository root: $repoRoot`nCaller directory: $callerDirectory`nTarget (literal data): $target`n"
        Push-Location -LiteralPath $repoRoot -ErrorAction Stop
        $pushed = $true
        if ($mode -eq 'diff-study') {
            $gitCommands = @(
                @{ Label = 'Git status (including untracked names)'; Args = @('-c', 'core.quotePath=true', 'status', '--short', '--untracked-files=all') },
                @{ Label = 'Staged patch: HEAD -> index'; Args = @('diff', '--no-ext-diff', '--no-textconv', '--no-color', '--cached', '--') },
                @{ Label = 'Unstaged patch: index -> working tree'; Args = @('diff', '--no-ext-diff', '--no-textconv', '--no-color', '--') }
            )
            foreach ($gitCommand in $gitCommands) {
                $gitArgs = @('--no-optional-locks') + $gitCommand.Args
                $gitOutput = & git @gitArgs
                if ($LASTEXITCODE -ne 0) { throw "Git inspection failed: $($gitCommand.Label)" }
                $context += "`n## $($gitCommand.Label)`n" + ($gitOutput -join "`n") + "`n"
            }
        }
        New-Item -ItemType Directory -Path $contextDirectory -ErrorAction Stop | Out-Null
        [IO.File]::WriteAllText($contextFile, $context, [Text.UTF8Encoding]::new($false))
        $launchPrompt = "Read the study instructions and context in $contextFile, then begin the requested study. Stay read-only for the entire conversation."
        Write-Host "ai: opening $candidate study session"
        switch ($candidate) {
            'codex' {
                & $backend.Source --sandbox read-only --ask-for-approval never --cd $repoRoot -- $launchPrompt
            }
            'claude' {
                & $backend.Source --permission-mode plan --tools 'Read,Glob,Grep' --disallowedTools 'mcp__*' --add-dir $contextDirectory -- $launchPrompt
            }
            'opencode' {
                $externalDirectories = @{}
                $externalPath = $contextDirectory.Replace('\', '/')
                $externalDirectories[$externalPath] = 'allow'
                $externalDirectories[($externalPath + '/*')] = 'allow'
                $env:OPENCODE_CONFIG_CONTENT = @{
                    agent = @{
                        'ai-study' = @{
                            mode = 'primary'
                            description = 'Read-only repository study'
                            permission = @{
                                '*' = 'deny'; read = 'allow'; glob = 'allow'; grep = 'allow'
                                question = 'allow'; bash = 'deny'; edit = 'deny'
                                external_directory = $externalDirectories
                            }
                        }
                    }
                } | ConvertTo-Json -Depth 8 -Compress
                & $backend.Source --agent ai-study --prompt $launchPrompt
            }
        }
        $result = $LASTEXITCODE
        if ($result -ne 0) {
            Write-Error "ai: $candidate exited with status $result" -ErrorAction Continue
        }
    }
    catch {
        Write-Error "ai: $($_.Exception.Message)" -ErrorAction Continue
        $result = 1
    }
    finally {
        if ($pushed) { Pop-Location }
        $env:OPENCODE_CONFIG_CONTENT = $oldOpenCodeConfig
        if (Test-Path -LiteralPath $contextFile) { Remove-Item -LiteralPath $contextFile -Force }
        if (Test-Path -LiteralPath $contextDirectory) { Remove-Item -LiteralPath $contextDirectory }
        $global:LASTEXITCODE = $result
    }
}
