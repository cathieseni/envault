"""Retention policy: automatically purge secrets older than a configured age."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.storage import get_project_dir
from envault.audit import log_event
from envault.history import get_history
from envault.secrets import delete_secret, list_secrets


def _get_retention_path(project: str) -> Path:
    return get_project_dir(project) / "retention.json"


def _load_retention(project: str) -> Dict:
    path = _get_retention_path(project)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_retention(project: str, data: Dict) -> None:
    path = _get_retention_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_retention(project: str, max_age_days: int) -> None:
    """Set the retention policy (max age in days) for a project."""
    if max_age_days <= 0:
        raise ValueError("max_age_days must be a positive integer")
    data = _load_retention(project)
    data["max_age_days"] = max_age_days
    _save_retention(project, data)
    log_event(project, "retention_set", {"max_age_days": max_age_days})


def get_retention(project: str) -> Optional[int]:
    """Return the configured max_age_days, or None if not set."""
    return _load_retention(project).get("max_age_days")


def clear_retention(project: str) -> None:
    """Remove the retention policy for a project."""
    path = _get_retention_path(project)
    if path.exists():
        path.unlink()
    log_event(project, "retention_cleared", {})


def apply_retention(project: str) -> List[str]:
    """Delete secrets whose last-set timestamp exceeds max_age_days.

    Returns the list of keys that were purged.
    """
    max_age_days = get_retention(project)
    if max_age_days is None:
        return []

    cutoff = time.time() - max_age_days * 86400
    purged: List[str] = []

    for key in list_secrets(project):
        history = get_history(project, key)
        if not history:
            continue
        last_entry = history[-1]
        last_ts = last_entry.get("timestamp", 0)
        if last_ts < cutoff:
            delete_secret(project, key)
            purged.append(key)
            log_event(project, "retention_purged", {"key": key, "last_ts": last_ts})

    return purged
