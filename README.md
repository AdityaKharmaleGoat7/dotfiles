# Dotfiles

This repository keeps shared terminal and Git settings in one place on macOS
and Windows. The setup scripts connect them to the configuration already in
your home directory without replacing unrelated settings.

## macOS

Review the files first, then run:

```sh
brew bundle --file ./Brewfile
./install.sh
```

Restart the terminal or reload the shell configuration:

```sh
source ~/.zshrc
```

The installer is safe to run again. It adds:

- a marked block in `~/.zshrc` that loads `zsh/zshrc`
- an `include.path` in `~/.gitconfig` that loads `git/config`
- a link from `~/.config/starship.toml` to `starship/starship.toml`
- a link from `~/.config/btop/btop.conf` to `btop/btop.conf`

Starship is started by the tracked Zsh configuration. The installer removes an
equivalent standalone Starship startup line from `~/.zshrc` to prevent duplicate
prompts. After uninstalling, reload Zsh with `exec zsh` to return to its normal
prompt.

## System monitoring

Run the terminal resource monitor from anywhere:

```sh
btop
```

The tracked dashboard shows CPU, Apple GPU, memory, and process utilization.
It refreshes every two seconds. Press `q` to exit. Settings changed inside btop
are saved to the tracked configuration and can be committed with Git.

On Apple M5 hardware, GPU utilization, power, and memory are supported. GPU
temperature may display `0 °C` because of an upstream sensor compatibility
issue.

If a Starship configuration already exists, the installer preserves it as
`~/.config/starship.toml.pre-dotfiles`. Uninstalling restores that file.

## Local and private settings

Put machine-specific or private shell settings in `~/.zshrc.local`. For
example, API keys and work-only paths belong there rather than in this
repository.

Keep your Git name and email in the existing global config:

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Uninstall

```sh
./install.sh --uninstall
```

This removes the shell block and Git include, restores previous Starship and
btop configurations when backups exist, and leaves this repository and
Homebrew packages in place.

## Windows

Use Windows 10 or 11 and run the installer from PowerShell as a normal user:

```powershell
.\install.ps1
```

If Windows blocks local PowerShell scripts, use the one-time execution-policy
override:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer uses Winget to install Git, PowerShell 7, Starship, and the
Microsoft Visual C++ runtime. It installs Scoop when needed and uses it to
install the GPU-enabled `btop-lhm` package. Running the installer again is
safe.

Open a new PowerShell 7 terminal after installation. The `g`, `gs`, `ll`, and
`la` commands and the shared Starship prompt work from every directory. Run
Windows Terminal as Administrator before starting `btop` when you want GPU and
temperature information; `btop-lhm` requires elevation for those sensors.

Windows btop uses its own tracked configuration because btop4win has a
different format from the macOS version. Scoop persists this configuration
across package upgrades. If the repository and Scoop are on the same drive,
btop changes update the tracked file directly. Otherwise, rerun
`.\install.ps1` after editing `btop/windows/btop.conf` to synchronize it.

Machine-specific or private PowerShell settings belong in:

```text
~/.config/powershell/profile.local.ps1
```

Uninstall the managed Windows configuration with:

```powershell
.\install.ps1 --uninstall
```

This removes the managed PowerShell block and Git include and restores any
previous btop configuration. Installed packages remain available.

## Adding another tool

Create a directory for the tool, add its configuration, and update
`install.sh` to link or include it. Never commit passwords, tokens, private
keys, or cloud credentials.
