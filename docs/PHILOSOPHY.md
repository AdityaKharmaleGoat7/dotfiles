# Philosophy

How changes get made in this repo, whether the hands typing are human or an
AI agent. Read this before writing any code. [`AGENTS.md`](../AGENTS.md)
layers stricter, mechanical rules on top of this for AI agents
specifically; this document is the shared baseline both follow.

## Match the change to the ask

Do what was requested, sized to what was requested. A bug fix doesn't carry
a refactor with it; a one-line config change doesn't need a new abstraction
around it. Don't fix unrelated things you notice along the way, raise them
instead.

## Simplicity over cleverness

Prefer the boring, obvious solution. Three similar lines beat a premature
abstraction built for a fourth case that doesn't exist yet. Don't add
config options, flags, or error handling for situations that can't happen
in this repo (see `config/<tool>` in the Repo conventions below for the
concrete example).

## Verify behavior, not just syntax

A script that parses is not a script that works. Before calling a change
done, run the check that actually exercises the behavior that changed, not
just a linter or parser. `AGENTS.md`'s verification table is the mechanical
form of this rule for the installers specifically.

## Prefer reversible steps

Favor actions you can undo over actions you can't. Stash or move work
aside instead of deleting it; ask before force-pushing, resetting history,
or anything else that destroys state rather than changing it. If you're
unsure whether something is safe to discard, treat it as someone's
in-progress work until proven otherwise.

## Say why once, in one place

Code comments say only what's needed to edit that exact line. The
reasoning behind a decision, the alternatives considered, and the history
of what went wrong before, go in [`DECISIONS.md`](DECISIONS.md) instead.
Two copies of the same rationale drift apart; one copy doesn't.

## Never commit secrets

Passwords, tokens, private keys, and cloud credentials never go in this
repository, tracked or not. Machine-specific or private settings go in
untracked `*.local` files outside the repo (see the README's "Local and
private settings" sections).
