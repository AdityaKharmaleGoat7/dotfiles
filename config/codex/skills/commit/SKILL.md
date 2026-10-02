---
name: commit
description: "Writes a Conventional Commits message and makes a Git commit. Always use this when asked to \"commit\", \"write a commit message\", or \"commit the changes\"."
---

# Git commit skill

## Gather context

Run these directly, without a helper script:

- `git status --short --branch`
- `git diff HEAD`
- `git branch --show-current`
- `git log --oneline -10`

Split the diff into logical units; don't mix the user's changes with unrelated ones.

## Execute

1. Write the message following Conventional Commits.
2. Choose a type from `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
   `test`, `build`, `ci`, `chore`.
3. Subject line: imperative mood, 72 characters or fewer, no trailing period.
4. If only asked for the message, present the target files and the message, then stop.
5. If asked to commit, stage the target files by explicit path. Staging is
   reversible, so no approval is needed yet.

   ```bash
   git add -- <target files...>
   ```

6. **Approval before committing**: present the staged contents
   (`git status --short`) and the full commit message, and get the user's
   approval. The point is to confirm the message; if it isn't approved,
   don't commit, revise per the feedback, and present it again. If the
   caller's own instructions already treat the `git commit` permission
   prompt as the approval step, follow that instead of stopping to ask
   again. If the caller hands you an already-approved message verbatim,
   use it unchanged.
7. Commit after approval. Don't chain `git add` with `&&`; rules don't
   parse inside a shell compound, so chaining it defeats the prompt.

   ```bash
   git commit -m '<subject>' -m '<body>'
   ```

8. After committing, confirm the result with `git status --short` and
   `git log -1 --oneline`.

## Forbidden

- Bypassing hooks with `--no-verify` or similar
- Adding unrelated changes via `git add .` / `git add -A`
- Adding unrelated changes via `git commit -a` / `git commit --all`
- `git commit --amend` without an explicit request
- Unmeasured numeric claims
