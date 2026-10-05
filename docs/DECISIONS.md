# Decisions

Rationale for non-obvious choices in this repo. Code comments say only what's
needed to edit that line; the "why" (context, alternatives, history) lives
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
`Get-Command` first, with the hardcoded path only as a fallback, the same
pattern already used for `git` and `starship`.

## Scoop's `config root_path` output needs `6>$null`, not just `2>$null`

When no custom Scoop root is configured, `scoop config root_path` prints
`'root_path' is not set` through PowerShell's information stream (stream 6),
not stderr. `2>$null` alone didn't suppress it, so it leaked into the
installer's output even though the fallback path logic was already correct.

## LazyGit's winget fallback path points at `WinGet\Packages\`, not `WinGet\Links\`

`Get-CommandPath` needs a fallback path for tools winget just installed,
since the current process's `PATH` doesn't pick up winget's update until a
new shell starts (the same reason `starship` and `uv` already have
fallbacks). Starship's fallback is
`WinGet\Links\starship.exe`, so `JesseDuffield.lazygit`'s fallback was
written the same way at first. Installing it for real and checking showed
`WinGet\Links\` is empty on this machine; winget actually extracted it to
`WinGet\Packages\JesseDuffield.lazygit_Microsoft.Winget.Source_8wekyb3d8bbwe\lazygit.exe`.
The fallback now points there instead. (The `8wekyb3d8bbwe` suffix is a fixed
Microsoft publisher ID winget's own source packaging uses, not something
random per machine or per install, so this exact path is expected to be
stable.)

## `config/lazygit/config.yml` forces `gui.language: en`

LazyGit's default `gui.language: auto` picks a UI language from the OS
locale. On Windows that's `GetUserDefaultLocaleName`, i.e. the Region/format
setting, not the display language; a machine with an English display
language but a Japanese Region setting (as on the machine this was found on)
gets a Japanese LazyGit UI with no indication why. Forcing `en` makes the
language the same on every machine regardless of that machine's locale, same
reasoning as pinning any other environment-dependent default.

## LazyGit's config path differs by OS, unlike every other tool tracked here

Every other tool in `config/` resolves to the same kind of path on
Linux/WSL and macOS (`$XDG_CONFIG_HOME` or `~/.config`), so `install.sh`
could use one `config_home` variable for all of them. LazyGit's own docs
specify different defaults per OS: `~/.config/lazygit` on Linux,
`~/Library/Application Support/lazygit` on macOS (overridable by setting
`XDG_CONFIG_HOME`, which LazyGit does honor on macOS, just not by default),
and `%LOCALAPPDATA%\lazygit` on Windows, confirmed by running
`lazygit --print-config-dir` on this repo's Windows machine, since it's easy
to assume `%APPDATA%` (Roaming) by analogy with Zed and get it wrong.
`install.sh` branches on `uname` (and checks `XDG_CONFIG_HOME` first) only
for this one tool; `install.ps1` just hardcodes `$env:LOCALAPPDATA`.

## tmux is not installed or linked by `install.ps1`

tmux has no official native Windows build. Managing it from the Windows
installer would mean linking a config for a binary that isn't really
supported there. Windows users who want tmux run it inside WSL instead
(documented in the README); `install.sh` on WSL/macOS/Linux handles the real
install and link.

## Codex's AGENTS.md goes to `~/.codex`, not `$XDG_CONFIG_HOME`

Unlike every other tool tracked here (Starship, btop, Zed, LazyGit on
Linux/macOS), Codex CLI doesn't put its config under
`$XDG_CONFIG_HOME`/`~/.config`; it uses a plain `~/.codex` directory on
every OS, the same style as `~/.ssh` or `~/.tmux.conf`. Confirmed by
inspecting an existing `~/.codex` on a machine with Codex CLI actually
installed: it already contained a `skills/.system/` folder with Codex's
own marker file at that exact path, with no `$XDG_CONFIG_HOME` override
set. `install.sh` and `install.ps1` both link straight into `$HOME/.codex`
(`%USERPROFILE%\.codex` on Windows) rather than reusing `config_home`.

`config.toml`, however, mixes user settings with session state in the
same file and has no comment-stripped-JSON-style merge tool here the way
Zed's settings do; managing it would need a TOML merge mechanism this
repo doesn't have yet, so it was left alone rather than guessed at.

## Codex's rules/ and skills/ are linked per-file, not per-directory

`rules/*.rules` (command-approval policy, one file per tool) and
`skills/*/SKILL.md` (task playbooks) are linked individually, one entry
per file, rather than linking either directory as a whole: a real
`~/.codex/skills/` on a machine with Codex actually installed already had
a `.system/` subdirectory of Codex's own built-in skills, so replacing the
whole `skills/` directory with a symlink to this repo's `config/codex/skills`
would hide that. install.sh and install.ps1 each needed a generic
per-item link helper to do this without an install/uninstall function
pair per rule and per skill (`install_codex_link` in install.sh;
`Install-ManagedHardLink`, already generic, reused in install.ps1).

## `install.ps1`'s Dust fallback path is discovered, not hardcoded

Every other Winget-installed tool here (Starship, uv, LazyGit, eza) ends up
at a fallback path that's stable across versions, keyed only by the
package's publisher ID (the `8wekyb3d8bbwe` suffix from the LazyGit
decision above). Dust breaks that pattern: Winget extracts its release zip
with the version baked into the folder name
(`dust-v1.2.5-x86_64-pc-windows-gnu\dust.exe`), confirmed by actually
installing it and inspecting
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\bootandy.dust_...\`. A literal
fallback path would silently go stale on the next Dust version bump: the
idempotency check would stop finding the binary, call `winget install`
again, and that call then fails outright, since re-running `winget install`
on an already-current package exits non-zero (`43`, "No available upgrade
found") instead of a no-op success. `Get-DustPath` searches the package
directory for `dust.exe` at runtime instead of guessing the subfolder name,
so it keeps working across Dust version bumps without needing a repo update.

## `config/zed/settings.json` omits the `proxy` setting

The live settings.json this was tracked from had `"proxy":
"http://wrcproxy.ad.melco.co.jp:9515"`, a corporate proxy specific to one
machine/network. It isn't a credential, but it's still machine-specific, and
AGENTS.md routes machine-specific settings to untracked `*.local` files. The
proxy line was dropped from the tracked file; machine-specific Zed settings
now go through the merge mechanism below instead.

## Zed's settings.json is generated by merging a gitignored overlay, not linked

Zed's settings.json has no include mechanism, so unlike `~/.zshrc.local` or
`~/.tmux.conf.local`, a local override can't be a separate file Zed itself
reads. The installers (`install.sh`, `install.ps1`) merge the tracked
`config/zed/settings.json` with `config/zed/settings.local.json` (gitignored,
created by hand per machine, holds the proxy or anything else machine-specific)
and write the result to Zed's config directory with a "generated, do not edit"
comment on the first line. This is why Zed's file is the one tool config in
this repo that's generated at install time instead of symlinked or
hardlinked, and why editing it (or Zed's own settings UI) only lasts until the
next install, unlike every other tracked config here. `jq` does the merge on
`install.sh` (`.[0] * .[1]`, recursive, overlay wins on conflicts); `install.ps1`
does the equivalent by hand with `PSCustomObject` property merging instead of
`ConvertFrom-Json -AsHashtable`, because `-AsHashtable` is PowerShell 7+ only
and this script also has to run under Windows PowerShell 5.1.

Both settings.json and the merge overlay carry Zed's `//` comment-style
header, which standard JSON parsers (`jq`, `ConvertFrom-Json`) reject, so both
installers strip lines matching `^\s*//` before parsing.

## `install.sh` strips the `zed` cask line from the Brewfile on Linux

Homebrew Cask only supports macOS; running `brew bundle --file Brewfile`
with the Linuxbrew `brew` installed would fail to resolve `cask "zed"`.
`install_packages` now checks `uname` and, on anything other than Darwin,
copies the Brewfile to a temp file with `cask ` lines removed before
calling `brew bundle` on that copy, printing a note that Zed needs a
separate install. This keeps one Brewfile as the source of truth instead
of forking it per OS. `install_zed`'s existing "Zed is not installed" hint
is also branched on `uname`, since its old message (`brew bundle --file
Brewfile`) would send a Linux user straight back into the same cask
failure.

## `config/zsh/zshrc` adds `/home/linuxbrew/.linuxbrew/bin` to `path`

The existing Homebrew `path` entry only covered
`/opt/homebrew/bin` (Apple Silicon macOS). Homebrew on Linux
(Linuxbrew) installs to `/home/linuxbrew/.linuxbrew` instead, and that
directory isn't on `PATH` by default the way `/usr/local/bin` (Intel
macOS Homebrew) typically already is. Without this entry, every
Homebrew-installed tool in the Brewfile (btop, dust, eza, jq, lazygit,
starship, tmux, uv) would install successfully on Linux but stay
invisible to the shell.

## `third_party/` is gitignored, not a submodule

It's a scratch space for cloning other people's repos to read for reference
(e.g. a colleague's dotfiles for comparison). A submodule or committed copy
would version repos we don't maintain and bloat this repo for no benefit.
Nothing in `third_party/` is meant to ship with these dotfiles.

## `install.sh` installs the Brewfile and migrates former config paths

The Windows installer already installs its required packages, while macOS
previously required a separate `brew bundle` command before `install.sh`.
That split made a successful configuration run look like it had installed
tools such as eza when it had not. The macOS installer now runs the tracked
Brewfile first, giving both platforms a one-command setup after their package
manager is available. Uninstall still leaves packages in place.

The move from top-level tool directories to `config/<tool>` also left existing
Zsh loaders, Git includes, and symlinks pointing at paths that no longer
exist. The installer recognizes only those exact former repository paths and
updates them without replacing the preserved `.pre-dotfiles` backups. Other
unexpected targets continue to stop installation rather than being assumed
safe to overwrite.
