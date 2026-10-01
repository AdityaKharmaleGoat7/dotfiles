# Shared PowerShell settings managed by the dotfiles repository.

$configRoot = Split-Path -Parent $PSScriptRoot
$env:STARSHIP_CONFIG = Join-Path $configRoot "starship\starship.toml"

Set-Alias -Name g -Value git -Scope Global

function global:gs {
    git status --short --branch @args
}

function global:ll {
    Get-ChildItem -Force @args
}

function global:la {
    Get-ChildItem -Force -Name @args
}

$localProfile = Join-Path $HOME ".config\powershell\profile.local.ps1"
if (Test-Path -LiteralPath $localProfile) {
    . $localProfile
}

if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}

