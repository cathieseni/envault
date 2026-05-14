"""Per-secret value history tracking for envault."""

import json
import time
from pathlib import Path
from typing import List, Dict, Any

from envault.storage import get_project_dir

MAX_HISTORY = 50


def _get_history_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "history.json"


def _load_history(project_name: str) -> Dict[str, List[Dict[str, Any]]]:
    path = _get_history_path(project_name)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_history(project_name: str, data: Dict[str, List[Dict[str, Any]]]) -> None:
    path = _get_history_path(project_name)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def record_change(project_name: str, key: str, old_value: str, new_value: str, actor: str = "cli") -> None:
    """Append a history entry for a secret value change."""
    data = _load_history(project_name)
    entries = data.get(key, [])
    entries.append({
        "timestamp": time.time(),
        "old_value": old_value,
        "new_value": new_value,
        "actor": actor,
    })
    if len(entries) > MAX_HISTORY:
        entries = entries[-MAX_HISTORY:]
    data[key] = entries
    _save_history(project_name, data)


def get_history(project_name: str, key: str) -> List[Dict[str, Any]]:
    """Return the change history for a specific secret key."""
    data = _load_history(project_name)
    if key not in data:
        raise KeyError(f"No history found for key '{key}' in project '{project_name}'.")
    return data[key]


def clear_history(project_name: str, key: str) -> None:
    """Clear history entries for a specific key."""
    data = _load_history(project_name)
    if key in data:
        del data[key]
        _save_history(project_name, data)


def all_history(project_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Return all history entries for a project."""
    return _load_history(project_name)
