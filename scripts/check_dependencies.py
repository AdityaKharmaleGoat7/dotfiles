#!/usr/bin/env python3
"""Check whether this repo's declared Python packages are installed."""

import importlib.metadata
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?=\[|[<>=!~;\s@]|$)")


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def add_requirement(requirement, source, found):
    match = NAME.match(requirement.strip())
    if not match:
        raise ValueError(f"Unsupported dependency entry in {source}")
    name = match.group(1)
    key = normalized(name)
    if key not in found:
        found[key] = (name, [])
    found[key][1].append(source)


def read_pyproject(path, found):
    if tomllib is None:
        raise ValueError("Reading pyproject.toml requires Python 3.11 or newer")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    if any(name in project.get("dynamic", []) for name in ("dependencies", "optional-dependencies")):
        raise ValueError("pyproject.toml declares dynamic dependencies; inspect its build configuration")
    for requirement in project.get("dependencies", []):
        add_requirement(requirement, "pyproject.toml [project]", found)
    for extra, requirements in project.get("optional-dependencies", {}).items():
        for requirement in requirements:
            add_requirement(requirement, f"pyproject.toml [{extra}]", found)

    groups = data.get("dependency-groups", {})

    def read_group(group, stack=()):
        if group not in groups:
            raise ValueError(f"Unknown dependency group: {group}")
        if group in stack:
            raise ValueError(f"Circular dependency group: {' -> '.join((*stack, group))}")
        for entry in groups[group]:
            if isinstance(entry, str):
                add_requirement(entry, f"pyproject.toml [{group}]", found)
            elif isinstance(entry, dict) and set(entry) == {"include-group"}:
                read_group(entry["include-group"], (*stack, group))
            else:
                raise ValueError(f"Unsupported entry in dependency group {group}")

    for group in groups:
        read_group(group)

    poetry = data.get("tool", {}).get("poetry", {})
    poetry_sections = {
        "main": poetry.get("dependencies", {}),
        "dev": poetry.get("dev-dependencies", {}),
    }
    for group, details in poetry.get("group", {}).items():
        poetry_sections[group] = details.get("dependencies", {})
    for group, dependencies in poetry_sections.items():
        for name in dependencies:
            if name.lower() != "python":
                add_requirement(name, f"pyproject.toml [poetry.{group}]", found)


def read_requirements(path, found, seen):
    path = path.resolve()
    if path in seen:
        return
    seen.add(path)
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip().split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ")):
            read_requirements(path.parent / line.split(maxsplit=1)[1], found, seen)
        elif line.startswith(("-c ", "--constraint ")):
            continue
        elif line.startswith((
            "--index-url ", "--extra-index-url ", "--trusted-host ",
            "--find-links ", "--no-index",
        )):
            continue
        else:
            add_requirement(line, f"{path.name}:{number}", found)


def main():
    repo = Path.cwd()
    manifests = [repo / name for name in ("pyproject.toml", "requirements.txt", "requirement.txt")]
    manifests = [path for path in manifests if path.is_file()]
    if not manifests:
        print("No pyproject.toml, requirements.txt, or requirement.txt found in this directory.")
        return 2

    found = {}
    try:
        for path in manifests:
            if path.name == "pyproject.toml":
                read_pyproject(path, found)
            else:
                read_requirements(path, found, set())
    except (OSError, ValueError) as error:
        print(f"Cannot check dependencies: {error}")
        return 2

    installed = {
        normalized(distribution.metadata["Name"]): distribution.version
        for distribution in importlib.metadata.distributions()
        if distribution.metadata.get("Name")
    }
    missing = False
    for key, (name, sources) in sorted(found.items()):
        version = installed.get(key)
        if version is None:
            missing = True
            print(f"MISSING {name} ({', '.join(sources)})")
        else:
            print(f"INSTALLED {name}=={version} ({', '.join(sources)})")
    if not found:
        print("No dependencies declared in the detected files.")
    return int(missing)


if __name__ == "__main__":
    raise SystemExit(main())
