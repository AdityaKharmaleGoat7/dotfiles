#!/usr/bin/env python3
"""Find running processes matching app names or command text."""

import argparse
import csv
import io
import os
import subprocess


def processes():
    if os.name == "nt":
        output = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, check=True
        ).stdout
        for row in csv.reader(io.StringIO(output)):
            if len(row) >= 2:
                yield row[1], row[0]
    else:
        output = subprocess.run(
            ["ps", "-axo", "pid=,args="], capture_output=True, text=True, check=True
        ).stdout
        for line in output.splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) == 2:
                yield parts[0], parts[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("terms", nargs="+", help="case-insensitive process search terms")
    args = parser.parse_args()

    matches = []
    for pid, command in processes():
        if pid != str(os.getpid()) and any(term.lower() in command.lower() for term in args.terms):
            matches.append((pid, command))

    for pid, command in matches:
        print(f"{pid}  {command}")
    if not matches:
        print("No matching processes found.")
    return int(not matches)


if __name__ == "__main__":
    raise SystemExit(main())
