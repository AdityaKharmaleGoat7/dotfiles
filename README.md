# Dotfiles

This repository keeps shared terminal and Git settings in one place. The setup
script connects them to the configuration already in your home directory; it
does not replace your existing `.zshrc` or `.gitconfig`.

## Install

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

## Adding another tool

Create a directory for the tool, add its configuration, and update
`install.sh` to link or include it. Never commit passwords, tokens, private
keys, or cloud credentials.
