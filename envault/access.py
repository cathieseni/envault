"""Per-project access control: define which keys a named profile can read."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.storage import get_project_dir, load_secrets

_ACCESS_FILE = "access.json"


def _get_access_path(project: str) -> Path:
    return get_project_dir(project) / _ACCESS_FILE


def _load_access(project: str) -> Dict[str, List[str]]:
    path = _get_access_path(project)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_access(project: str, data: Dict[str, List[str]]) -> None:
    path = _get_access_path(project)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def grant(project: str, profile: str, key: str) -> None:
    """Grant *profile* read access to *key* in *project*."""
    secrets = load_secrets(project)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project}'.")
    data = _load_access(project)
    data.setdefault(profile, [])
    if key not in data[profile]:
        data[profile].append(key)
    _save_access(project, data)


def revoke(project: str, profile: str, key: str) -> None:
    """Revoke *profile* access to *key* in *project*."""
    data = _load_access(project)
    if profile not in data or key not in data[profile]:
        raise KeyError(f"Profile '{profile}' has no access to '{key}'.")
    data[profile].remove(key)
    if not data[profile]:
        del data[profile]
    _save_access(project, data)


def list_profile_keys(project: str, profile: str) -> List[str]:
    """Return keys accessible by *profile*."""
    data = _load_access(project)
    return list(data.get(profile, []))


def list_profiles(project: str) -> List[str]:
    """Return all profiles defined for *project*."""
    return list(_load_access(project).keys())


def can_access(project: str, profile: str, key: str) -> bool:
    """Return True if *profile* may read *key*."""
    return key in _load_access(project).get(profile, [])
