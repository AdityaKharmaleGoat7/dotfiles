# Shared PowerShell settings managed by the dotfiles repository.

$configRoot = Split-Path -Parent $PSScriptRoot
$env:STARSHIP_CONFIG = Join-Path $configRoot "starship\starship.toml"

. (Join-Path $configRoot "ai/ai.ps1")

Set-Alias -Name g -Value git -Scope Global

function global:gs {
    git status --short --branch @args
}

if (Get-Command eza -ErrorAction SilentlyContinue) {
    function global:ll {
        eza -lah --git @args
    }

    function global:la {
        eza -a @args
    }
} else {
    function global:ll {
        Get-ChildItem -Force @args
    }

    function global:la {
        Get-ChildItem -Force -Name @args
    }
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
    (& uv generate-shell-completion powershell) | Out-String | Invoke-Expression
}

$localProfile = Join-Path $HOME ".config\powershell\profile.local.ps1"
if (Test-Path -LiteralPath $localProfile) {
    . $localProfile
}

if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}

