# Dotfiles

Shared shell, Git, and tool settings for macOS, Linux, and Windows.
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

### Linux

Requires Homebrew. Packages are listed in [`Brewfile`](Brewfile); the
installer skips the `zed` cask entry, since Homebrew Cask only supports
macOS.

```sh
./install.sh
source ~/.zshrc
```

Install Zed separately; the installer still generates and links its
settings.

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
- tmux on macOS and Linux; Windows users can use tmux through WSL.
- Zed settings and shared Zed / Codex / Claude Code agent instructions, rules,
  and skills.

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
ai explain event loop
ai trace handle_request
ai why src/main.py
ai diff-study
ai quiz "request lifecycle"
ai --help
```

`ai` selects Codex, then Claude Code, then OpenCode based on availability.
Sessions inspect code with edits disabled; `diff-study` explains staged and
unstaged changes. `ai explain` accepts files or general topics, including
multiword topics. Keep the session open to ask follow-up questions. Study
replies aim for ASD-STE100-style English in about 80% of explanatory prose;
this is a writing preference, not certified compliance. Quote paths and other
targets containing spaces. Prompts live in
[`config/ai/`](config/ai/).

## Project diagnostics

The scripts in [`scripts/`](scripts/) inspect the Python environment,
declared dependencies, imports, local TCP ports, and running processes. Run them
from the repository you are working on so `debug_env.py` reports that working
directory. Use that project's Python interpreter (or activate its virtual
environment first).

In Zsh, open a new terminal or run `source ~/.zshrc`, then use the aliases from
any repository:

```sh
pydebug
deps
pyimports requests pytest
pyports 8000 5432
pyprocs uvicorn postgres
```

On macOS or Linux, set the path to this dotfiles checkout once in your shell:

```sh
DOTFILES_DIR="$HOME/path/to/dotfiles"
python3 "$DOTFILES_DIR/scripts/debug_env.py"
python3 "$DOTFILES_DIR/scripts/check_dependencies.py"
python3 "$DOTFILES_DIR/scripts/check_imports.py" requests pytest
python3 "$DOTFILES_DIR/scripts/check_ports.py" 8000 5432
python3 "$DOTFILES_DIR/scripts/check_processes.py" uvicorn postgres
```

On Windows PowerShell:

```powershell
$dotfilesDir = "C:\path\to\dotfiles"
python "$dotfilesDir/scripts/debug_env.py"
python "$dotfilesDir/scripts/check_dependencies.py"
python "$dotfilesDir/scripts/check_imports.py" requests pytest
python "$dotfilesDir/scripts/check_ports.py" 8000 5432
python "$dotfilesDir/scripts/check_processes.py" uvicorn postgres
```

`deps` checks packages declared in `pyproject.toml`, `requirements.txt`,
`requirement.txt`, and `package.json`. Python packages are checked in the
current Python installation; Node packages are checked in local or parent
`node_modules` directories. It includes development and optional dependencies
and required peer dependencies, reports whether each package is present, and
does not install packages or validate version constraints. The existing
`pydeps` alias also runs this checker. Reading `pyproject.toml` requires
Python 3.11 or newer.

The checker uses a limited, dependency-free requirements parser. It accepts
package names, extras, version specifier syntax, and named direct references
(`name @ URL`). It checks the base distribution only; extras do not trigger
checks of their transitive dependencies. Environment markers, editable or
unnamed local/archive dependencies, and remote requirements includes are
unsupported and produce an error rather than a potentially misleading result.

Local requirements includes support `-r file`, `-rfile`, and
`--requirement=file`, relative to the including file. Repeated includes and
include cycles are read once. Continuation lines and hash options are accepted;
constraints and supported index options are ignored. Dependency-group names
are normalized for comparison; conflicting names and group cycles are errors.

All declared Python extras/groups and Node optional dependencies are checked,
even if you did not install them. Optional Node peers are excluded. Node lookup
requires local or parent `node_modules`; Yarn Plug'n'Play is unsupported.
Exit codes are `0` for all packages present or no declared dependencies, `1`
for missing packages, and `2` for invalid/unsupported input or no manifests.
If `pyproject.toml` exists, Python older than 3.11 reports an error even when
other manifests are present. Use the project's interpreter; do not switch to
a different Python installation just to obtain TOML support. The `deps` and
`pydeps` aliases are Zsh-only; PowerShell users use the explicit commands above.

Replace the module names, TCP ports, and process terms with those used by your
project. `check_ports.py` tests binding to `127.0.0.1` by default; pass
`--host 0.0.0.0` to check all local IPv4 interfaces. Import, port, and process
checks exit with a nonzero status when a requested check fails or no matching
process is found. The environment report masks likely credential variables
and proxy values, but review it before sharing. On Windows, the process check
matches executable names; on macOS and Linux, it also searches command lines.

## Uninstall

macOS or Linux:

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

Dependency-checker tests (standard library only; use Python 3.11+ to include
TOML parsing tests):

```sh
python3 -m unittest discover -s tests -p 'test_check_dependencies.py' -v
```

```powershell
python -m unittest discover -s tests -p 'test_check_dependencies.py' -v
```

AI command-routing tests (no AI service required):

```sh
zsh -f tests/ai.zsh
```

```powershell
pwsh -NoProfile -File tests/ai.ps1
```
