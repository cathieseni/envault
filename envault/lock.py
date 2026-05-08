"""Per-project secret locking: prevent accidental modification of specific secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.storage import get_project_dir
from envault.project import get_project


def _get_lock_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "locks.json"


def _load_locks(project_name: str) -> List[str]:
    path = _get_lock_path(project_name)
    if not path.exists():
        return []
    with path.open() as f:
        return json.load(f)


def _save_locks(project_name: str, locks: List[str]) -> None:
    path = _get_lock_path(project_name)
    with path.open("w") as f:
        json.dump(locks, f, indent=2)


def lock_secret(project_name: str, key: str) -> None:
    """Mark a secret key as locked (read-only)."""
    get_project(project_name)  # raises if missing
    locks = _load_locks(project_name)
    if key not in locks:
        locks.append(key)
        _save_locks(project_name, locks)


def unlock_secret(project_name: str, key: str) -> None:
    """Remove the lock from a secret key."""
    get_project(project_name)
    locks = _load_locks(project_name)
    if key not in locks:
        raise KeyError(f"Key '{key}' is not locked in project '{project_name}'.")
    locks.remove(key)
    _save_locks(project_name, locks)


def is_locked(project_name: str, key: str) -> bool:
    """Return True if the given key is locked."""
    return key in _load_locks(project_name)


def list_locked(project_name: str) -> List[str]:
    """Return all locked keys for a project."""
    get_project(project_name)
    return list(_load_locks(project_name))


def assert_not_locked(project_name: str, key: str) -> None:
    """Raise RuntimeError if the key is locked."""
    if is_locked(project_name, key):
        raise RuntimeError(
            f"Secret '{key}' in project '{project_name}' is locked and cannot be modified."
        )
