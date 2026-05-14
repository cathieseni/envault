"""Watchlist: mark secrets for monitoring and detect value staleness."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_watchlist_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "watchlist.json"


def _load_watchlist(project_name: str) -> Dict[str, dict]:
    path = _get_watchlist_path(project_name)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_watchlist(project_name: str, data: Dict[str, dict]) -> None:
    path = _get_watchlist_path(project_name)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def watch_secret(project_name: str, key: str, max_age_days: float = 30.0) -> None:
    """Add a secret to the watchlist with an optional max-age threshold (in days)."""
    secrets = list_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    data = _load_watchlist(project_name)
    if key not in data:
        data[key] = {"watched_at": time.time(), "max_age_days": max_age_days}
    else:
        data[key]["max_age_days"] = max_age_days
    _save_watchlist(project_name, data)


def unwatch_secret(project_name: str, key: str) -> None:
    """Remove a secret from the watchlist."""
    data = _load_watchlist(project_name)
    if key not in data:
        raise KeyError(f"Secret '{key}' is not on the watchlist for project '{project_name}'.")
    del data[key]
    _save_watchlist(project_name, data)


def list_watched(project_name: str) -> List[str]:
    """Return all keys currently on the watchlist."""
    return list(_load_watchlist(project_name).keys())


def is_watched(project_name: str, key: str) -> bool:
    return key in _load_watchlist(project_name)


def stale_secrets(project_name: str) -> List[Dict]:
    """Return watched secrets whose age exceeds their configured max_age_days."""
    data = _load_watchlist(project_name)
    now = time.time()
    stale = []
    for key, meta in data.items():
        age_days = (now - meta["watched_at"]) / 86400
        if age_days > meta["max_age_days"]:
            stale.append({
                "key": key,
                "age_days": round(age_days, 2),
                "max_age_days": meta["max_age_days"],
            })
    return stale


def refresh_watch(project_name: str, key: str) -> None:
    """Reset the watched_at timestamp for a secret (e.g. after rotation)."""
    data = _load_watchlist(project_name)
    if key not in data:
        raise KeyError(f"Secret '{key}' is not on the watchlist for project '{project_name}'.")
    data[key]["watched_at"] = time.time()
    _save_watchlist(project_name, data)
