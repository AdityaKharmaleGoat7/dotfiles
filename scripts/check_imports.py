#!/usr/bin/env python3
"""Check imports in the current Python environment."""

import argparse
import importlib
import os
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("modules", nargs="+", help="module names to import")
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())
    failed = False
    for name in args.modules:
        try:
            importlib.import_module(name)
        except Exception as error:
            failed = True
            print(f"FAIL {name}: {type(error).__name__}: {error}")
        else:
            print(f"OK   {name}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
