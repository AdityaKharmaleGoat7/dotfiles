# Decisions

Rationale for non-obvious choices in this repo. Code comments say only what's
needed to edit that line; the "why" — context, alternatives, history — lives
here instead, so comments and reasoning don't drift out of sync.

## `config/<tool>` layout instead of one top-level folder per tool

A one-folder-per-tool layout (`btop/`, `git/`, `starship/`, ...) grows the
repo root forever as tools are added. Collapsing everything under `config/`
caps the root at a fixed set of entries; new tools add a subfolder inside
`config/` instead of a new top-level one.

## PowerShell 7 detection resolves `pwsh` via `Get-Command`, not a hardcoded path

`install.ps1` originally checked only
`$env:ProgramFiles\PowerShell\7\pwsh.exe`. On a machine where PowerShell 7 was
installed via winget, `pwsh` resolved through the `WindowsApps` alias instead,
so the hardcoded check missed it, winget was asked to install an
already-current package, and the script threw. `Get-PwshPath` now checks
`Get-Command` first, with the hardcoded path only as a fallback — the same
pattern already used for `git` and `starship`.

## Scoop's `config root_path` output needs `6>$null`, not just `2>$null`

When no custom Scoop root is configured, `scoop config root_path` prints
`'root_path' is not set` through PowerShell's information stream (stream 6),
not stderr. `2>$null` alone didn't suppress it, so it leaked into the
installer's output even though the fallback path logic was already correct.

## tmux is not installed or linked by `install.ps1`

tmux has no official native Windows build. Managing it from the Windows
installer would mean linking a config for a binary that isn't really
supported there. Windows users who want tmux run it inside WSL instead
(documented in the README); `install.sh` on WSL/macOS/Linux handles the real
install and link.

## `third_party/` is gitignored, not a submodule

It's a scratch space for cloning other people's repos to read for reference
(e.g. a colleague's dotfiles for comparison). A submodule or committed copy
would version repos we don't maintain and bloat this repo for no benefit —
nothing in `third_party/` is meant to ship with these dotfiles.
