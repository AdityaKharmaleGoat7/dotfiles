"""Classify staged Git changes with Jev."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from client import JevClient, JevError

MAX_DIFF_CHARS = 60000


def staged_diff(repo: Path) -> str:
    proc = subprocess.run(
        ["git", "diff", "--cached", "--no-ext-diff"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def classify(diff: str, client: JevClient | None = None) -> dict:
    if not diff.strip():
        raise ValueError("No staged changes found. Run git add first.")
    if len(diff) > MAX_DIFF_CHARS:
        raise ValueError(f"Staged diff exceeds {MAX_DIFF_CHARS} characters. Stage a smaller change.")

    client = client or JevClient()
    result = client.decide(
        state={"staged_git_diff": diff},
        questions={
            "risk": {
                "type": "choice",
                "instructions": "Classify the regression risk of committing these staged changes.",
                "criteria": {
                    "low": "Small or isolated change with low regression risk.",
                    "medium": "Meaningful change that deserves careful review or targeted tests.",
                    "high": "Potentially breaking, security-sensitive, destructive, or wide-impact change.",
                },
            }
        },
    )
    answer = result["answers"].get("risk")
    if (
        not isinstance(answer, dict)
        or answer.get("type") != "choice"
        or answer.get("choice") not in ("low", "medium", "high")
    ):
        raise JevError("Jev API returned an invalid risk choice.")
    return result


def main() -> int:
    try:
        result = classify(staged_diff(Path.cwd()))
    except (ValueError, JevError, subprocess.CalledProcessError) as exc:
        print(f"jev-risk: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
