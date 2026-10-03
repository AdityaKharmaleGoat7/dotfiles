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

### Proxy settings

Keep proxy settings in the local files above. Never put proxy credentials in
files inside this repository, including gitignored files. For Zsh, add the
following to `~/.zshrc.local`:

```sh
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="$HTTP_PROXY"
export NO_PROXY="localhost,127.0.0.1,.example.com"

# Some command-line tools only read the lowercase names.
export http_proxy="$HTTP_PROXY"
export https_proxy="$HTTPS_PROXY"
export no_proxy="$NO_PROXY"
```

For PowerShell, add the equivalent values to
`~/.config/powershell/profile.local.ps1`:

```powershell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = $env:HTTP_PROXY
$env:NO_PROXY = "localhost,127.0.0.1,.example.com"
```

Replace the example address and bypass list for the current network. Before
the first install, load the local file in the current shell so package-manager
processes can inherit the proxy settings:

```sh
source ~/.zshrc.local
```

```powershell
. "$HOME/.config/powershell/profile.local.ps1"
```

Zed reads these environment variables and also supports an explicit proxy
setting. To use the setting, create `config/zed/settings.local.json` with:

```json
{
  "proxy": "http://proxy.example.com:8080"
}
```

Rerun the installer after changing the Zed override.

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

## Python diagnostics

The scripts in [`scripts/`](scripts/) inspect the Python environment,
imports, local TCP ports, and running processes. Run them from the repository
you are working on so `debug_env.py` reports that working directory. Use that
project's Python interpreter (or activate its virtual environment first).

In Zsh, open a new terminal or run `source ~/.zshrc`, then use the aliases from
any repository:

```sh
pydebug
pyimports requests pytest
pyports 8000 5432
pyprocs uvicorn postgres
```

On macOS or Linux, set the path to this dotfiles checkout once in your shell:

```sh
DOTFILES_DIR="$HOME/path/to/dotfiles"
python3 "$DOTFILES_DIR/scripts/debug_env.py"
python3 "$DOTFILES_DIR/scripts/check_imports.py" requests pytest
python3 "$DOTFILES_DIR/scripts/check_ports.py" 8000 5432
python3 "$DOTFILES_DIR/scripts/check_processes.py" uvicorn postgres
```

On Windows PowerShell:

```powershell
$dotfilesDir = "C:\path\to\dotfiles"
python "$dotfilesDir/scripts/debug_env.py"
python "$dotfilesDir/scripts/check_imports.py" requests pytest
python "$dotfilesDir/scripts/check_ports.py" 8000 5432
python "$dotfilesDir/scripts/check_processes.py" uvicorn postgres
```

Replace the module names, TCP ports, and process terms with those used by your
project. `check_ports.py` tests binding to `127.0.0.1` by default; pass
`--host 0.0.0.0` to check all local IPv4 interfaces. Import, port, and process
checks exit with a nonzero status when a requested check fails or no matching
process is found. The environment report masks likely credential variables
and proxy values, but review it before sharing. On Windows, the process check
matches executable names; on macOS and Linux, it also searches command lines.

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
