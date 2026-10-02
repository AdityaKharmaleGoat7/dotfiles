# Study the current diff

The context contains a launch-time snapshot of Git status, staged changes
(HEAD to index), and unstaged changes (index to working tree). Analyze the two
patches separately, then explain their combined effect. The same file may
have different staged and working-tree versions. Binary markers do not show
binary contents. Untracked filenames are listed, but their contents are not
included; ask before studying those files.

Begin with the architectural context of the changed code. Explain:

1. What changed.
2. Old behavior, supported by removed code and surrounding context.
3. New behavior, supported by added code and surrounding context.
4. Why it changed: recorded evidence, inferred motivation, or unknown.
5. Important files/functions and their callers or dependencies.
6. Possible side effects, compatibility changes, and unverified risks.
7. What the learner should understand before committing, including which
   changes are staged and which will not be committed yet.

Inspect surrounding source as needed. Do not confuse the current working
tree with the staged version. Do not claim tests passed or suggest that all
visible changes are already staged. If context is too large to analyze fully,
state what remains unreviewed. If there are no tracked changes, say so.
