# Dotfiles

Shared shell, Git, and tool settings for macOS and Windows.
Configurations live in [`config/`](config/).

## Install

Review the configuration first, then run from this repository. Both installers
install missing tools and can be rerun safely.

### macOS

Requires Homebrew. Packages are listed in [`Brewfile`](Brewfile).

```sh
./install.sh
source ~/.zshrc
```

### Windows

Requires Windows 10 or 11. Run as a normal user from PowerShell:

```powershell
.\install.ps1
```

If local scripts are blocked:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

After installation, fully quit and relaunch your terminal to refresh `PATH`,
then use **PowerShell 7 (`pwsh`)**. The older Windows PowerShell profile is
not configured. Packages are installed through Winget and Scoop.

## What's included

- Zsh / PowerShell profiles, Starship prompt, and shared Git aliases.
- LazyGit (`g ui`), Git graph (`g lg`), and directory listings (`ll`, `la`).
- `uv` for Python projects, `dust` for disk usage, and `btop` for monitoring.
  Windows `btop` requires an Administrator terminal.
- tmux on macOS; Windows users can use tmux through WSL.
- Zed settings and shared Zed / Codex agent instructions, rules, and skills.

Set your Git identity separately:

```sh
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## Local and private settings

Keep secrets out of this repository. Use these files for private or
machine-specific settings:

| Settings | File |
| --- | --- |
| Zsh | `~/.zshrc.local` |
| tmux | `~/.tmux.conf.local` |
| PowerShell | `~/.config/powershell/profile.local.ps1` |
| Zed overrides | `config/zed/settings.local.json` (gitignored; non-secret settings only) |

Zed settings are generated from `config/zed/settings.json` plus the local
overrides. Local keys win and nested objects merge. Rerun the installer after
editing either file; direct edits in Zed's settings UI are overwritten.

## AI study mode

Install and authenticate Codex, Claude Code, or OpenCode separately, then run
from any Git working tree:

```sh
ai study
ai architecture
ai explain src/main.py
ai trace handle_request
ai why src/main.py
ai diff-study
ai quiz "request lifecycle"
ai --help
```

`ai` selects Codex, then Claude Code, then OpenCode based on availability.
Sessions inspect code with edits disabled; `diff-study` explains staged and
unstaged changes. Quote paths or topics containing spaces. Prompts live in
[`config/ai/`](config/ai/).

## Uninstall

macOS:

```sh
./install.sh --uninstall
exec zsh
```

Windows:

```powershell
.\install.ps1 --uninstall
```

Removes managed configuration and restores backups where available. Installed
packages and this repository remain.

## Contributing

Put new tool configurations under `config/<tool>` and update the relevant
installer. Read [Philosophy](docs/PHILOSOPHY.md) and [agent rules](AGENTS.md);
background and rationale live in [Decisions](docs/DECISIONS.md).

AI command-routing tests (no AI service required):

```sh
zsh -f tests/ai.zsh
```

```powershell
pwsh -NoProfile -File tests/ai.ps1
```

## License

[MIT](LICENSE).
