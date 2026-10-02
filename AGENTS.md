# AGENTS.md

Rules for AI coding agents working in this repo. Read
[`docs/PHILOSOPHY.md`](docs/PHILOSOPHY.md) first; it's the shared baseline
for humans and agents alike. This file layers stricter, mechanical rules on
top, for AI agents specifically. Rationale and history for any of these
live in [`docs/DECISIONS.md`](docs/DECISIONS.md), not here.

## Verification

Run the check that matches what changed, and show its output as evidence
before reporting the change done.

| Changed | Command |
| --- | --- |
| `install.sh` | `sh -n install.sh` |
| `install.ps1` | `powershell -NoProfile -Command "$e=$null; $null = [System.Management.Automation.Language.Parser]::ParseFile('install.ps1', [ref]$null, [ref]$e); if ($e) { $e } else { 'OK' }"` |
| either installer, behavior | run it against an isolated `$HOME`/`$XDG_CONFIG_HOME` (a `mktemp -d`), not the real one, and check both the first run and a second idempotent run |

A syntax check passing is not the same as the installer working. Both bugs
fixed in this repo so far (`pwsh` detection, Scoop's `root_path` output)
were syntax-valid and behaviorally wrong.

## Stop and report, don't route around a denial

If a permission prompt, hook, or confirmation rejects an action, switch to
an approach that's actually allowed. Don't disguise or split the command,
use working-directory tricks, or reach for a bypass flag to get around the
rejection. If there's no allowed way to do it, stop and report instead.

## Repo conventions

- Tool configuration lives under `config/<tool>`, not a new top-level
  folder per tool.
- Code comments say only what's needed to edit that exact line; rationale,
  alternatives, and history go in `docs/DECISIONS.md` instead.
- Never commit passwords, tokens, private keys, or cloud credentials.
  Machine-specific or private settings belong in untracked `*.local` files
  outside the repo (see README's "Local and private settings" sections).
