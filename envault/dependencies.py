"""Secret dependency tracking: define which secrets depend on others.

When a secret is rotated or deleted, dependents can be queried so the
caller can take appropriate action (warn, cascade-rotate, etc.).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_dep_path(project: str) -> Path:
    return get_project_dir(project) / "dependencies.json"


def _load_deps(project: str) -> Dict[str, List[str]]:
    path = _get_dep_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_deps(project: str, data: Dict[str, List[str]]) -> None:
    _get_dep_path(project).write_text(json.dumps(data, indent=2))


def add_dependency(project: str, key: str, depends_on: str) -> None:
    """Record that *key* depends on *depends_on* within *project*."""
    existing_keys = list_secrets(project)
    if key not in existing_keys:
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    if depends_on not in existing_keys:
        raise KeyError(f"Secret '{depends_on}' not found in project '{project}'")
    if key == depends_on:
        raise ValueError("A secret cannot depend on itself")

    data = _load_deps(project)
    deps = data.setdefault(depends_on, [])
    if key not in deps:
        deps.append(key)
    _save_deps(project, data)


def remove_dependency(project: str, key: str, depends_on: str) -> None:
    """Remove the recorded dependency of *key* on *depends_on*."""
    data = _load_deps(project)
    deps = data.get(depends_on, [])
    if key not in deps:
        raise KeyError(
            f"No dependency of '{key}' on '{depends_on}' in project '{project}'"
        )
    deps.remove(key)
    if not deps:
        del data[depends_on]
    _save_deps(project, data)


def get_dependents(project: str, key: str) -> List[str]:
    """Return all secrets that depend on *key*."""
    return list(_load_deps(project).get(key, []))


def get_dependencies(project: str, key: str) -> List[str]:
    """Return all secrets that *key* directly depends on."""
    data = _load_deps(project)
    return [parent for parent, children in data.items() if key in children]


def clear_dependencies(project: str, key: str) -> None:
    """Remove all dependency records that involve *key* (as parent or child)."""
    data = _load_deps(project)
    # Remove as parent
    data.pop(key, None)
    # Remove as child
    for parent in list(data.keys()):
        if key in data[parent]:
            data[parent].remove(key)
            if not data[parent]:
                del data[parent]
    _save_deps(project, data)
