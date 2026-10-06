#!/usr/bin/env python3
"""Check whether this repo's declared Python and Node packages are installed."""

import importlib.metadata
import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


PACKAGE_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
SPECIFIER = r"(?:===|==|!=|~=|<=|>=|<|>)\s*[A-Za-z0-9.*+!_-]+"
REQUIREMENT = re.compile(
    rf"({PACKAGE_NAME})(?:\s*\[\s*{PACKAGE_NAME}(?:\s*,\s*{PACKAGE_NAME})*\s*\])?"
    rf"\s*(?:@\s*[A-Za-z][A-Za-z0-9+.-]*://[^\s;]+|{SPECIFIER}(?:\s*,\s*{SPECIFIER})*|"
    rf"\(\s*{SPECIFIER}(?:\s*,\s*{SPECIFIER})*\s*\))?\s*"
)


def mapping(value, source):
    if not isinstance(value, dict):
        raise ValueError(f"Expected a table/object in {source}")
    return value


def sequence(value, source):
    if not isinstance(value, list):
        raise ValueError(f"Expected an array in {source}")
    return value


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def add_requirement(requirement, source, found):
    if not isinstance(requirement, str):
        raise ValueError(f"Expected a dependency string in {source}")
    if ";" in requirement:
        raise ValueError(f"Environment markers are unsupported in {source}")
    text = requirement.strip()
    if re.search(r"\.(?:whl|zip|tar\.gz|tar\.bz2|tgz)$", text, re.IGNORECASE):
        if "@" not in text:
            raise ValueError(f"Unnamed archives are unsupported in {source}")
    match = REQUIREMENT.fullmatch(text)
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
    project = mapping(data.get("project", {}), "pyproject.toml [project]")
    dynamic = sequence(project.get("dynamic", []), "pyproject.toml [project.dynamic]")
    if any(not isinstance(name, str) for name in dynamic):
        raise ValueError("Expected strings in pyproject.toml [project.dynamic]")
    if any(name in dynamic for name in ("dependencies", "optional-dependencies")):
        raise ValueError("pyproject.toml declares dynamic dependencies; inspect its build configuration")
    for requirement in sequence(project.get("dependencies", []), "pyproject.toml [project.dependencies]"):
        add_requirement(requirement, "pyproject.toml [project]", found)
    extras = mapping(project.get("optional-dependencies", {}), "pyproject.toml [project.optional-dependencies]")
    for extra, requirements in extras.items():
        for requirement in sequence(requirements, f"pyproject.toml [{extra}]"):
            add_requirement(requirement, f"pyproject.toml [{extra}]", found)

    groups = {}
    for name, entries in mapping(data.get("dependency-groups", {}), "pyproject.toml [dependency-groups]").items():
        if not re.fullmatch(PACKAGE_NAME, name):
            raise ValueError(f"Invalid dependency group name: {name}")
        key = normalized(name)
        if key in groups:
            raise ValueError(f"Duplicate normalized dependency group: {name}")
        groups[key] = (name, sequence(entries, f"pyproject.toml [{name}]"))

    def read_group(group, stack=()):
        if group not in groups:
            raise ValueError(f"Unknown dependency group: {group}")
        if group in stack:
            raise ValueError(f"Circular dependency group: {' -> '.join((*stack, group))}")
        original, entries = groups[group]
        for entry in entries:
            if isinstance(entry, str):
                add_requirement(entry, f"pyproject.toml [{original}]", found)
            elif isinstance(entry, dict) and set(entry) == {"include-group"}:
                included = entry["include-group"]
                if not isinstance(included, str) or not re.fullmatch(PACKAGE_NAME, included):
                    raise ValueError(f"Invalid include-group in {original}")
                read_group(normalized(included), (*stack, group))
            else:
                raise ValueError(f"Unsupported entry in dependency group {group}")

    for group in groups:
        read_group(group)

    tool = mapping(data.get("tool", {}), "pyproject.toml [tool]")
    poetry = mapping(tool.get("poetry", {}), "pyproject.toml [tool.poetry]")
    poetry_sections = [
        ("main", poetry.get("dependencies", {})),
        ("dev", poetry.get("dev-dependencies", {})),
    ]
    for group, details in mapping(poetry.get("group", {}), "pyproject.toml [tool.poetry.group]").items():
        details = mapping(details, f"pyproject.toml [poetry.{group}]")
        poetry_sections.append((group, details.get("dependencies", {})))
    for group, dependencies in poetry_sections:
        for name in mapping(dependencies, f"pyproject.toml [poetry.{group}]"):
            if name.lower() != "python":
                if not re.fullmatch(PACKAGE_NAME, name):
                    raise ValueError(f"Invalid Poetry package name in {group}")
                add_requirement(name, f"pyproject.toml [poetry.{group}]", found)


def read_requirements(path, found, seen):
    path = path.resolve()
    if path in seen:
        return
    seen.add(path)
    pending = ""
    start = 1
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not pending:
            start = number
        pending += raw
        if pending.endswith("\\"):
            pending = pending[:-1] + " "
            continue
        line = re.sub(r"(^|\s+)#.*$", "", pending).strip()
        pending = ""
        if not line:
            continue
        source = f"{path}:{start}"
        option = re.fullmatch(r"(-r|-c)\s*(.+)|(--requirement|--constraint)(?:\s+|=)(.+)", line)
        if option:
            flag = option.group(1) or option.group(3)
            target = (option.group(2) or option.group(4)).strip()
            if len(target) >= 2 and target[0] == target[-1] and target[0] in "\"'":
                target = target[1:-1]
            if not target:
                raise ValueError(f"Missing include path in {source}")
            if flag in ("-r", "--requirement"):
                if re.match(r"[A-Za-z][A-Za-z0-9+.-]*://", target):
                    raise ValueError(f"Remote includes are unsupported in {source}")
                read_requirements(path.parent / target, found, seen)
        elif re.fullmatch(r"--(?:index-url|extra-index-url|trusted-host|find-links)(?:\s+|=).+|--no-index", line):
            continue
        else:
            line = re.sub(r"\s+--hash(?:=|\s+)[A-Za-z0-9_-]+:[A-Fa-f0-9]+", "", line)
            add_requirement(line, source, found)
    if pending:
        raise ValueError(f"Unterminated continuation in {path}:{start}")


def read_package_json(path):
    data = mapping(json.loads(path.read_text(encoding="utf-8-sig")), "package.json")
    found = {}
    optional_peers = mapping(data.get("peerDependenciesMeta", {}), "package.json [peerDependenciesMeta]")
    for name, meta in optional_peers.items():
        meta = mapping(meta, f"package.json [peerDependenciesMeta.{name}]")
        if "optional" in meta and not isinstance(meta["optional"], bool):
            raise ValueError(f"Expected boolean optional flag for {name}")
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        for name, declaration in mapping(data.get(section, {}), f"package.json [{section}]").items():
            if not isinstance(declaration, str):
                raise ValueError(f"Expected a dependency string in package.json [{section}.{name}]")
            if section == "peerDependencies" and optional_peers.get(name, {}).get("optional"):
                continue
            parts = name.lstrip("@").split("/")
            if (not re.fullmatch(r"(?:@[A-Za-z0-9._-]+/)?[A-Za-z0-9._-]+", name)
                    or any(part in (".", "..") for part in parts)):
                raise ValueError(f"Unsupported package name in package.json [{section}]")
            found.setdefault(name, []).append(section)
    return found


def installed_node_package(repo, name):
    for directory in (repo, *repo.parents):
        package_file = directory / "node_modules" / name / "package.json"
        if package_file.is_file():
            return package_file
    return None


def main():
    repo = Path.cwd()
    manifests = [
        repo / name for name in
        ("pyproject.toml", "requirements.txt", "requirement.txt", "package.json")
    ]
    manifests = [path for path in manifests if path.is_file()]
    if not manifests:
        print("No pyproject.toml, requirements.txt, requirement.txt, or package.json found here.")
        return 2

    python_packages = {}
    node_packages = {}
    seen = set()
    try:
        for path in manifests:
            if path.name == "pyproject.toml":
                read_pyproject(path, python_packages)
            elif path.name == "package.json":
                node_packages = read_package_json(path)
            else:
                read_requirements(path, python_packages, seen)
    except (OSError, ValueError) as error:
        print(f"Cannot check dependencies: {error}")
        return 2

    installed_python = {
        normalized(distribution.metadata["Name"]): distribution.version
        for distribution in importlib.metadata.distributions()
        if distribution.metadata.get("Name")
    }
    missing = False
    for key, (name, sources) in sorted(python_packages.items()):
        version = installed_python.get(key)
        if version is None:
            missing = True
            print(f"MISSING {name} ({', '.join(sources)})")
        else:
            print(f"INSTALLED {name}=={version} ({', '.join(sources)})")
    for name, sections in sorted(node_packages.items()):
        package_file = installed_node_package(repo, name)
        if package_file is None:
            missing = True
            print(f"MISSING {name} (package.json [{', '.join(sections)}])")
        else:
            print(f"INSTALLED {name} (package.json [{', '.join(sections)}])")
    if not python_packages and not node_packages:
        print("No dependencies declared in the detected files.")
    return int(missing)


if __name__ == "__main__":
    raise SystemExit(main())
