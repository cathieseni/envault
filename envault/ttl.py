"""TTL (time-to-live) management for secrets — auto-expire secrets after a set duration."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_ttl_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "ttl.json"


def _load_ttl(project_name: str) -> dict:
    path = _get_ttl_path(project_name)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_ttl(project_name: str, data: dict) -> None:
    path = _get_ttl_path(project_name)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def set_ttl(project_name: str, key: str, seconds: int) -> float:
    """Set a TTL for a secret key. Returns the absolute expiry timestamp."""
    keys = list_secrets(project_name)
    if key not in keys:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    if seconds <= 0:
        raise ValueError("TTL must be a positive number of seconds.")
    data = _load_ttl(project_name)
    expires_at = time.time() + seconds
    data[key] = {"seconds": seconds, "expires_at": expires_at}
    _save_ttl(project_name, data)
    return expires_at


def get_ttl(project_name: str, key: str) -> Optional[dict]:
    """Return TTL info for a key, or None if not set."""
    data = _load_ttl(project_name)
    return data.get(key)


def clear_ttl(project_name: str, key: str) -> bool:
    """Remove TTL for a key. Returns True if it existed, False otherwise."""
    data = _load_ttl(project_name)
    if key not in data:
        return False
    del data[key]
    _save_ttl(project_name, data)
    return True


def is_expired(project_name: str, key: str) -> bool:
    """Return True if the key has a TTL that has elapsed."""
    entry = get_ttl(project_name, key)
    if entry is None:
        return False
    return time.time() >= entry["expires_at"]


def get_expired_keys(project_name: str) -> list[str]:
    """Return all keys whose TTL has elapsed."""
    data = _load_ttl(project_name)
    now = time.time()
    return [k for k, v in data.items() if now >= v["expires_at"]]


def purge_expired(project_name: str) -> list[str]:
    """Delete all secrets whose TTL has elapsed. Returns list of purged keys."""
    from envault.secrets import delete_secret

    expired = get_expired_keys(project_name)
    for key in expired:
        try:
            delete_secret(project_name, key)
        except KeyError:
            pass
        clear_ttl(project_name, key)
    return expired
