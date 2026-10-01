# Dotfiles

This repository keeps shared terminal and Git settings in one place on macOS
and Windows. The setup scripts connect them to the configuration already in
your home directory without replacing unrelated settings. Each tool's
configuration lives under `config/<tool>`.

## 1) macOS

### Install

Review the files first, then run:

```sh
brew bundle --file ./Brewfile
./install.sh
```

Restart the terminal or reload the shell configuration:

```sh
source ~/.zshrc
```

The installer is safe to run again.

### What it manages

- a marked block in `~/.zshrc` that loads `config/zsh/zshrc`
- an `include.path` in `~/.gitconfig` that loads `config/git/config`
- a link from `~/.config/starship.toml` to `config/starship/starship.toml`
- a link from `~/.config/btop/btop.conf` to `config/btop/btop.conf`
- a link from `~/.tmux.conf` to `config/tmux/tmux.conf`

Starship is started by the tracked Zsh configuration. The installer removes an
equivalent standalone Starship startup line from `~/.zshrc` to prevent
duplicate prompts. After uninstalling, reload Zsh with `exec zsh` to return to
its normal prompt.

`uv`, the Python package and project manager, is installed by
`brew bundle --file ./Brewfile`. The tracked Zsh configuration registers its
completions when `uv` is on the `PATH`.

If a Starship configuration already existed, the installer preserved it as
`~/.config/starship.toml.pre-dotfiles`. Uninstalling restores that file.

### System monitoring

Run the terminal resource monitor from anywhere:

```sh
btop
```

The tracked dashboard shows CPU, Apple GPU, memory, and process utilization.
It refreshes every two seconds. Press `q` to exit. Settings changed inside
btop are saved to the tracked configuration and can be committed with Git.

On Apple M5 hardware, GPU utilization, power, and memory are supported. GPU
temperature may display `0 °C` because of an upstream sensor compatibility
issue.

### Terminal multiplexer

The tracked `tmux.conf` enables mouse support, vi-style copy mode, and
`|`/`-` splits, and reloads with the `r` key after the prefix. Start a session
with:

```sh
tmux
```

### Local and private settings

Put machine-specific or private shell settings in `~/.zshrc.local`, and
machine-specific tmux settings in `~/.tmux.conf.local`. For example, API keys
and work-only paths belong there rather than in this repository.

### Uninstall

```sh
./install.sh --uninstall
```

This removes the shell block and Git include, restores previous Starship,
btop, and tmux configurations when backups exist, and leaves this repository
and Homebrew packages in place.

## 2) Windows

### Install

Use Windows 10 or 11 and run the installer from PowerShell as a normal user:

```powershell
.\install.ps1
```

If Windows blocks local PowerShell scripts, use the one-time execution-policy
override:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer uses Winget to install Git, PowerShell 7, Starship, uv, and the
Microsoft Visual C++ runtime. It installs Scoop when needed and uses it to
install the GPU-enabled `btop-lhm` package. Running the installer again is
safe.

Open a new PowerShell 7 terminal after installation. The `g`, `gs`, `ll`, and
`la` commands, the shared Starship prompt, and `uv` shell completions work
from every directory.

### What it manages

- a marked block in PowerShell 7's `$PROFILE.CurrentUserAllHosts` that loads
  `config/powershell/profile.ps1`
- an `include.path` in the global Git config that loads `config/git/config`
- a hardlink (or a managed copy, if the repository and Scoop are on different
  drives) from `config/btop/windows/btop.conf` into Scoop's persisted
  `btop-lhm` configuration

### System monitoring

Run the terminal resource monitor from anywhere:

```powershell
btop
```

Run Windows Terminal as Administrator before starting `btop` when you want
GPU and temperature information; `btop-lhm` requires elevation for those
sensors.

Windows btop uses its own tracked configuration because btop4win has a
different format from the macOS version. Scoop persists this configuration
across package upgrades. If the repository and Scoop are on the same drive,
btop changes update the tracked file directly. Otherwise, rerun
`.\install.ps1` after editing `config/btop/windows/btop.conf` to synchronize
it.

### Terminal multiplexer

tmux has no native Windows build, so `install.ps1` does not install or link
it. To use the tracked `tmux.conf` on Windows, run tmux inside WSL:

```sh
wsl --install
sudo apt update && sudo apt install tmux
```

Then point `~/.tmux.conf` (inside WSL) at this repository's
`config/tmux/tmux.conf`, either by running `install.sh` from a WSL clone of
this repository or by linking to the Windows-mounted path under `/mnt/c/...`.
If you just want pane splitting without tmux, Windows Terminal's native panes
(`Alt+Shift+-` / `Alt+Shift+=`) need no extra setup.

### Local and private settings

Put machine-specific or private PowerShell settings in:

```text
~/.config/powershell/profile.local.ps1
```

### Uninstall

```powershell
.\install.ps1 --uninstall
```

This removes the managed PowerShell block and Git include and restores any
previous btop configuration. Installed packages remain available.

## Git identity

Keep your Git name and email in the existing global config on either
platform:

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Adding another tool

Create a directory for the tool under `config/`, add its configuration, and
update `install.sh` (and `install.ps1` for Windows-relevant tools) to link or
include it. Never commit passwords, tokens, private keys, or cloud
credentials.

## Comments and documentation

Code comments say only what's needed to edit that exact line, such as a
non-obvious constraint, a workaround, or a unit. Rationale, alternatives
considered, and the history behind a decision belong in
[`docs/DECISIONS.md`](docs/DECISIONS.md) instead, so the two don't drift out
of sync with each other.
