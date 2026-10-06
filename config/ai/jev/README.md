# Jev AI study

This directory is an isolated experiment for structured AI decisions in the dotfiles project. Jev is not required for installing or using the dotfiles.

## Setup

Create a Jev API key in your Jev account and expose it only as a local environment variable named `JEV_API_KEY`.

Do not put the key in this repository. The root `.gitignore` already excludes `.env`, `.env.*`, `*.secret`, and `*.local` files.

## First experiment: staged commit risk

Stage the changes you want to inspect and run:

```sh
git add <files>
python config/ai/jev/commit_risk.py
```

The script sends the staged diff as state and asks Jev to classify regression risk as `low`, `medium`, or `high`. It prints Jev's machine-readable response as JSON.

The diff is capped at 60,000 characters so an accidental large staged change does not send an unbounded payload.

## Architecture

- `client.py`: reusable standard-library HTTP client; reads `JEV_API_KEY` only at request time.
- `commit_risk.py`: useful Git-oriented experiment built on top of the client.
- `tests/test_jev.py`: local unit tests that mock the HTTP layer and never spend Jev credits.

## Decision rule

Use Jev when the result should be a constrained decision or classification. Use a coding agent or general LLM when the task needs open-ended reasoning, code generation, or explanation.

After enough real use, decide whether to keep, expand, or remove this integration.
