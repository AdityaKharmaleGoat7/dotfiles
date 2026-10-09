"""Suggest a tool for a task with Jev."""
from __future__ import annotations

import argparse
import json
import sys

from client import JevClient, JevError

MAX_REQUEST_CHARS = 60000
ROUTES = ("codex", "claude", "python", "shell")


def classify(request: str, client: JevClient | None = None) -> dict:
    if not request.strip():
        raise ValueError("Task request is empty. Describe the task to route.")
    if len(request) > MAX_REQUEST_CHARS:
        raise ValueError(f"Task request exceeds {MAX_REQUEST_CHARS} characters. Shorten the request.")

    client = client or JevClient()
    result = client.decide(
        state={"task_request": request},
        questions={
            "route": {
                "type": "choice",
                "instructions": (
                    "Suggest one tool for this task using the study policy. "
                    "Honor an explicitly requested tool first. Otherwise choose by "
                    "the work required, preferring shell for a simple command and "
                    "Python for repeatable data automation."
                ),
                "criteria": {
                    "codex": "Explicit Codex requests; otherwise repository code changes, debugging, or code review.",
                    "claude": "Explicit Claude requests; otherwise conceptual explanations, planning, or prose without code changes.",
                    "python": "Explicit Python automation requests; otherwise repeatable data processing needing loops, parsing, or transformations.",
                    "shell": "Explicit shell requests; otherwise a straightforward existing command or short pipeline for files, Git, or processes.",
                },
            }
        },
    )
    answer = result["answers"].get("route")
    if (
        not isinstance(answer, dict)
        or answer.get("type") != "choice"
        or answer.get("choice") not in ROUTES
    ):
        raise JevError("Jev API returned an invalid task route.")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Suggest a task route as JSON without executing it.")
    parser.add_argument("request", help="Task to classify; quote spaces.")
    args = parser.parse_args(argv)
    try:
        result = classify(args.request)
    except (ValueError, JevError) as exc:
        print(f"jev-route: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
