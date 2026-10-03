#!/usr/bin/env python3
"""Show the Python environment used to run this script."""

import importlib.metadata
import os
import platform
import sys
from pathlib import Path


def display_env(name, value):
    sensitive = (
        "TOKEN", "SECRET", "PASSWORD", "PASSWD", "KEY", "CREDENTIAL",
        "AUTH", "COOKIE", "PROXY", "URL", "DSN", "CONNECTION",
    )
    if any(part in name.upper() for part in sensitive):
        return "<redacted>"
    return value


def main():
    print(f"Python: {sys.version.split()[0]}")
    print(f"Executable: {sys.executable}")
    print(f"Environment prefix: {sys.prefix}")
    print(f"Base prefix: {sys.base_prefix}")
    print(f"OS: {platform.platform()}")
    print(f"Working directory: {Path.cwd()}")
    print(f"Home: {Path.home()}")
    print(f"Virtual environment: {os.environ.get('VIRTUAL_ENV', '(none)')}")
    print("Python import paths:")
    for path in sys.path:
        print(f"  {path or '(working directory)'}")
    print("PATH entries:")
    for path in os.environ.get("PATH", "").split(os.pathsep):
        print(f"  {path}")
    print("Environment variables:")
    for name, value in sorted(os.environ.items()):
        print(f"  {name}={display_env(name, value)}")
    print("Installed packages:")
    packages = sorted(
        (distribution.metadata.get("Name", "(unknown)"), distribution.version)
        for distribution in importlib.metadata.distributions()
    )
    for name, version in packages:
        print(f"  {name}=={version}")


if __name__ == "__main__":
    main()
