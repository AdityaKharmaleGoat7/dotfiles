# Jev AI study

This directory is an isolated experiment for structured AI decisions in the dotfiles project. Jev is not required for installing or using the dotfiles.

## What Jev does

[Jev's decision API](https://jev-ai.org/docs/) accepts state and typed questions.
It returns decisions rather than generated prose. This experiment uses a
`choice` question: named risk labels with descriptions, followed by a selected
label, probabilities, and confidence in the response. See the
[request contract](https://jev-ai.org/docs/decisions/) and
[question types](https://jev-ai.org/docs/question-types/).

## Setup

Use Python 3.10+; no third-party packages are required. Create a Jev API key
in your Jev account and expose it only as a local environment variable named
`JEV_API_KEY`. Read it from your local secret store or shell configuration;
never paste the key into a tracked file.

Do not put the key in this repository. The root `.gitignore` already excludes `.env`, `.env.*`, `*.secret`, and `*.local` files.

## First experiment: staged commit risk

Stage the changes you want to inspect and run:

```sh
git add <files>
python3 -B config/ai/jev/commit_risk.py
```

The script sends the staged diff as state and asks Jev to classify regression risk as `low`, `medium`, or `high`. It prints Jev's machine-readable response as JSON.

The command sends the staged diff to the external Jev service. Inspect what
you have staged before running it. Successful API calls use your Jev balance.
There are no automatic retries.

Diffs over 60,000 characters are rejected before the API call. Stage a smaller
change instead of classifying only part of a commit. This character limit
does not guarantee that a diff fits the model's token limit.

Success exits with status `0` and writes JSON to stdout. Failures exit with
status `2`, write diagnostics to stderr, and leave stdout empty. The returned
`answers.risk.choice` must be `low`, `medium`, or `high`. Confidence and
probabilities remain in the response for the reviewer to inspect; a risk label
does not approve a commit or replace tests.

## Examples and verification

[Example request](examples/commit_risk.request.json) shows the state and risk
question used by the classifier. [Example response](examples/commit_risk.response.json)
shows a synthetic answer, not an observed Jev result or accuracy measurement.

Run the tests from the repository root without an API key:

```sh
python3 -B -m unittest discover -s tests -p 'test_jev.py' -v
```

On Windows, use `python` instead of `python3`. The suite checks request shape,
authentication, malformed responses, transport errors, empty and oversized
diffs, risk labels, and CLI output. One test creates an isolated Git repository,
stages a file, changes it again without staging, and sends the staged diff
through a real local HTTP server. It exercises the Git-to-HTTP-to-JSON path
without sending repository data to Jev or spending credits.

For a live check, export `JEV_API_KEY` locally, stage a small non-sensitive
change, and run `python3 -B config/ai/jev/commit_risk.py`. Confirm `answers.risk.choice`
contains a valid label, inspect its probabilities, and record the response
model/version, latency, usage, and whether the label was useful. Compare several
representative diffs with human review and an ordinary structured-output LLM
call before claiming an accuracy, cost, or latency advantage.

## Architecture

- `client.py`: reusable standard-library HTTP client; reads `JEV_API_KEY` only at request time.
- `commit_risk.py`: useful Git-oriented experiment built on top of the client.
- `examples/`: synthetic request and response JSON for the first experiment.
- `tests/test_jev.py`: unit tests and a local Git/HTTP integration test; no Jev credits used.

## Decision rule

Use Jev when the result should be a constrained decision or classification
with probabilities. An ordinary LLM can also return structured output, but
this API directly exposes typed decisions and distributions. Use a coding
agent or general LLM when the task needs open-ended reasoning, code generation,
or an explanation. Actual quality and performance advantages need measurement.

## Study conclusion

**Keep** the isolated commit-risk experiment for now; do not expand it yet.
Local tests establish that the deterministic integration works, including
staged-only input and machine-readable output. They do not establish model
accuracy or a benefit over an ordinary LLM call.

Live verification remains pending: `JEV_API_KEY` was unavailable during this
study. The example response is synthetic. Keep this conclusion provisional
until real use provides evidence to expand or remove the experiment.

Task routing, debugging classification, and repository-health classification
are deferred until this first experiment proves useful. Neither installer nor
normal shell startup calls Jev.
