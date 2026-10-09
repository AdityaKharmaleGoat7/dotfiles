# Jev implementation summary

Jev has two standalone experiments in this repository: staged commit risk
classification and advisory task routing. Both reuse a Python client and
return structured JSON. They require Python 3.10+ and no third-party packages.

## Shared API client

[client.py](client.py) sends state and typed questions to Jev using HTTP POST.
It reads `JEV_API_KEY` from the environment when making a request and uses
Bearer authentication. Its default model is `jev-1.13`, with a 30-second
timeout.

The client checks the question count, parses JSON responses, and verifies
that the answers match the requested question names. HTTP and connection
errors produce diagnostics that omit raw exception details. There are no
automatic retries.

## Staged commit risk

[commit_risk.py](commit_risk.py) reads the staged Git diff and asks Jev to
classify regression risk as `low`, `medium`, or `high`.

Empty diffs and diffs over 60,000 characters are rejected before an API call.
Accepted diffs are sent in full. The classifier verifies that the response
contains a valid risk choice and preserves the remaining response metadata.

Run from the Git working tree after staging the intended changes:

```sh
python3 -B config/ai/jev/commit_risk.py
```

## Advisory task routing

[task_router.py](task_router.py) accepts a task description and asks Jev to
suggest `codex`, `claude`, `python`, or `shell`.

The study policy prioritizes explicitly requested tools. Otherwise, it assigns
repository coding work to Codex, explanations and prose to Claude, repeatable
data automation to Python, and simple commands or pipelines to shell. This
split is a local study convention, not a measured comparison of capabilities.

Empty requests and requests over 60,000 characters are rejected before an API
call. The returned route must be one of the four allowed labels. The command
prints a suggestion for human review and does not execute the task.

```sh
python3 -B config/ai/jev/task_router.py "List the files in the current directory."
```

## Output and examples

Both commands exit with status `0` and print JSON to stdout on success.
Classification failures exit with status `2`, print diagnostics to stderr,
and leave stdout empty.

The [examples directory](examples/) contains request and response JSON for
both experiments. Responses are synthetic examples, not recorded live results.
The [study README](README.md) contains setup instructions and evaluation steps.

## Verification

[tests/test_jev.py](../../../tests/test_jev.py) contains 19 tests covering
authentication, request limits, malformed responses, valid labels, CLI output,
and errors. Local HTTP integration tests exercise both experiments. The commit
risk test uses a temporary Git repository to verify that unstaged edits are
excluded. The routing test checks that task text is not executed.

```sh
python3 -B -m unittest discover -s tests -p 'test_jev.py' -v
```

These tests require no API key and spend no Jev credits. On Windows, use
`python` instead of `python3`.

## Current status

The deterministic integration has been tested locally. Live API verification
and measurements of accuracy, cost, and latency remain pending because
`JEV_API_KEY` was unavailable during implementation.

The current conclusion is to keep both isolated experiments for evaluation.
Debugging and repository health classifiers remain deferred. Neither
experiment is required by the installers or called during normal shell startup.
