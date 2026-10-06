"""Classify staged Git changes with Jev."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from client import JevClient, JevError


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

    client = client or JevClient()
    return client.decide(
        state={"staged_git_diff": diff[:60000]},
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


def main() -> int:
    try:
        result = classify(staged_diff(Path.cwd()))
    except (ValueError, JevError, subprocess.CalledProcessError) as exc:
        print(f"jev-risk: {exc}")
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
