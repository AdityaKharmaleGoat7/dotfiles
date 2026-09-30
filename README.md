# Dotfiles

This repository keeps shared terminal and Git settings in one place. The setup
script connects them to the configuration already in your home directory; it
does not replace your existing `.zshrc` or `.gitconfig`.

## Install

Review the files first, then run:

```sh
./install.sh
```

Restart the terminal or reload the shell configuration:

```sh
source ~/.zshrc
```

The installer is safe to run again. It adds:

- a marked block in `~/.zshrc` that loads `zsh/zshrc`
- an `include.path` in `~/.gitconfig` that loads `git/config`

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

This removes only the shell block and Git include created by the installer.
The files in this repository remain available.

## Adding another tool

Create a directory for the tool, add its configuration, and update
`install.sh` to link or include it. Never commit passwords, tokens, private
keys, or cloud credentials.

