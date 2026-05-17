"""Per-project trust levels for secrets: untrusted, pending, trusted, verified."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets

VALID_LEVELS = ("untrusted", "pending", "trusted", "verified")


def _get_trust_path(project: str) -> Path:
    return get_project_dir(project) / "trust.json"


def _load_trust(project: str) -> Dict[str, dict]:
    p = _get_trust_path(project)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_trust(project: str, data: Dict[str, dict]) -> None:
    _get_trust_path(project).write_text(json.dumps(data, indent=2))


def set_trust(project: str, key: str, level: str, note: str = "") -> dict:
    """Set the trust level for a secret key."""
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid trust level '{level}'. Choose from: {VALID_LEVELS}")
    keys = list_secrets(project)
    if key not in keys:
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    data = _load_trust(project)
    entry = {
        "level": level,
        "note": note,
        "updated_at": time.time(),
    }
    data[key] = entry
    _save_trust(project, data)
    return entry


def get_trust(project: str, key: str) -> Optional[dict]:
    """Return the trust entry for a key, or None if not set."""
    data = _load_trust(project)
    return data.get(key)


def remove_trust(project: str, key: str) -> bool:
    """Remove the trust entry for a key. Returns True if it existed."""
    data = _load_trust(project)
    if key not in data:
        return False
    del data[key]
    _save_trust(project, data)
    return True


def list_trust(project: str) -> Dict[str, dict]:
    """Return all trust entries for a project."""
    return dict(_load_trust(project))


def get_by_level(project: str, level: str) -> Dict[str, dict]:
    """Return all keys that have the given trust level."""
    if level not in VALID_LEVELS:
        raise ValueError(f"Invalid trust level '{level}'.")
    return {k: v for k, v in _load_trust(project).items() if v.get("level") == level}
