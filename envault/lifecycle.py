"""Secret lifecycle management: track creation, last-accessed, and last-modified timestamps."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir
from envault.project import get_project


def _get_lifecycle_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "lifecycle.json"


def _load_lifecycle(project_name: str) -> dict:
    path = _get_lifecycle_path(project_name)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_lifecycle(project_name: str, data: dict) -> None:
    path = _get_lifecycle_path(project_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def record_created(project_name: str, key: str) -> float:
    """Record the creation timestamp for a key (only sets if not already present)."""
    get_project(project_name)  # raises if missing
    data = _load_lifecycle(project_name)
    if key not in data:
        data[key] = {}
    if "created_at" not in data[key]:
        ts = time.time()
        data[key]["created_at"] = ts
        _save_lifecycle(project_name, data)
    return data[key]["created_at"]


def record_modified(project_name: str, key: str) -> float:
    """Update the last-modified timestamp for a key."""
    get_project(project_name)
    data = _load_lifecycle(project_name)
    if key not in data:
        data[key] = {}
    ts = time.time()
    data[key]["modified_at"] = ts
    _save_lifecycle(project_name, data)
    return ts


def record_accessed(project_name: str, key: str) -> float:
    """Update the last-accessed timestamp for a key."""
    get_project(project_name)
    data = _load_lifecycle(project_name)
    if key not in data:
        data[key] = {}
    ts = time.time()
    data[key]["accessed_at"] = ts
    _save_lifecycle(project_name, data)
    return ts


def get_lifecycle(project_name: str, key: str) -> Optional[dict]:
    """Return lifecycle timestamps for a key, or None if not tracked."""
    get_project(project_name)
    data = _load_lifecycle(project_name)
    return data.get(key)


def delete_lifecycle(project_name: str, key: str) -> bool:
    """Remove lifecycle tracking for a key. Returns True if entry existed."""
    get_project(project_name)
    data = _load_lifecycle(project_name)
    if key in data:
        del data[key]
        _save_lifecycle(project_name, data)
        return True
    return False


def list_lifecycle(project_name: str) -> dict:
    """Return the full lifecycle map for all tracked keys in a project."""
    get_project(project_name)
    return _load_lifecycle(project_name)
