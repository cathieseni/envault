"""Per-secret rotation scheduling: define how often a secret should be rotated."""

import json
import time
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_schedule_path(project: str) -> Path:
    return get_project_dir(project) / "schedule.json"


def _load_schedule(project: str) -> dict:
    path = _get_schedule_path(project)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_schedule(project: str, data: dict) -> None:
    path = _get_schedule_path(project)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def set_schedule(project: str, key: str, interval_seconds: int) -> dict:
    """Set a rotation schedule for a secret. interval_seconds must be > 0."""
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    keys = list_secrets(project)
    if key not in keys:
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    data = _load_schedule(project)
    entry = {
        "interval_seconds": interval_seconds,
        "last_rotated": data.get(key, {}).get("last_rotated", None),
        "next_rotation": time.time() + interval_seconds,
    }
    data[key] = entry
    _save_schedule(project, data)
    return entry


def get_schedule(project: str, key: str) -> Optional[dict]:
    """Return the schedule entry for a key, or None if not scheduled."""
    data = _load_schedule(project)
    return data.get(key)


def clear_schedule(project: str, key: str) -> None:
    """Remove the rotation schedule for a key."""
    data = _load_schedule(project)
    if key not in data:
        raise KeyError(f"No schedule found for key '{key}' in project '{project}'")
    del data[key]
    _save_schedule(project, data)


def list_scheduled(project: str) -> dict:
    """Return all scheduled keys and their entries for a project."""
    return dict(_load_schedule(project))


def due_keys(project: str) -> list:
    """Return keys whose next_rotation timestamp is in the past (due for rotation)."""
    now = time.time()
    data = _load_schedule(project)
    return [k for k, v in data.items() if v.get("next_rotation", float("inf")) <= now]


def mark_rotated(project: str, key: str) -> None:
    """Update last_rotated to now and advance next_rotation by interval."""
    data = _load_schedule(project)
    if key not in data:
        raise KeyError(f"No schedule found for key '{key}' in project '{project}'")
    now = time.time()
    entry = data[key]
    entry["last_rotated"] = now
    entry["next_rotation"] = now + entry["interval_seconds"]
    data[key] = entry
    _save_schedule(project, data)
