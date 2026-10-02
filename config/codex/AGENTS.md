# Global instructions

## Match the change to what was asked

Do what was requested, sized to what was requested. Don't fix unrelated
things you notice along the way or add scope that wasn't asked for; mention
them instead.

## Simplicity over cleverness

Prefer the boring, obvious solution. Don't add abstractions, config
options, or error handling for situations that can't happen.

## Verify behavior, not just syntax

Before reporting a change done, find and run the test, lint, or build the
project actually defines, and show its output as evidence. A syntax check
passing is not the same as the change working. Don't write up a result for
a check you didn't actually run.

## Prefer reversible steps

Favor actions you can undo over actions you can't. Stash or move work
aside instead of deleting it; ask before force-pushing, resetting history,
or anything else that destroys state rather than changes it.

## Stop and report, don't route around a denial

If a permission prompt, approval rule, or hook rejects an action, switch to
an approach that's actually allowed. Don't disguise or split the command,
use working-directory tricks, or reach for a bypass flag to get around the
rejection. If there's no allowed way to do it, stop and report instead.

## Never commit secrets

Passwords, tokens, private keys, and cloud credentials never go into a
repository, tracked or not.
