"""Secret grouping — organise secrets into named groups within a project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_group_path(project: str) -> Path:
    return get_project_dir(project) / "groups.json"


def _load_groups(project: str) -> Dict[str, List[str]]:
    path = _get_group_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_groups(project: str, data: Dict[str, List[str]]) -> None:
    _get_group_path(project).write_text(json.dumps(data, indent=2))


def add_to_group(project: str, group: str, key: str) -> None:
    """Add *key* to *group*.  Raises KeyError if key does not exist."""
    existing = list_secrets(project)
    if key not in existing:
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    data = _load_groups(project)
    members = data.setdefault(group, [])
    if key not in members:
        members.append(key)
    _save_groups(project, data)


def remove_from_group(project: str, group: str, key: str) -> None:
    """Remove *key* from *group*.  Raises KeyError if group or key absent."""
    data = _load_groups(project)
    if group not in data or key not in data[group]:
        raise KeyError(f"Key '{key}' not in group '{group}'")
    data[group].remove(key)
    if not data[group]:
        del data[group]
    _save_groups(project, data)


def list_groups(project: str) -> List[str]:
    """Return all group names for *project*."""
    return list(_load_groups(project).keys())


def get_group_members(project: str, group: str) -> List[str]:
    """Return keys belonging to *group*.  Returns empty list if group absent."""
    return _load_groups(project).get(group, [])


def delete_group(project: str, group: str) -> None:
    """Delete an entire group.  Raises KeyError if group does not exist."""
    data = _load_groups(project)
    if group not in data:
        raise KeyError(f"Group '{group}' not found in project '{project}'")
    del data[group]
    _save_groups(project, data)


def groups_for_key(project: str, key: str) -> List[str]:
    """Return every group that contains *key*."""
    data = _load_groups(project)
    return [g for g, members in data.items() if key in members]
