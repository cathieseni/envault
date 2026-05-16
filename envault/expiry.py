"""Secret expiry tracking — set TTL on secrets and detect expired/stale ones."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets

_EXPIRY_FILE = "expiry.json"


def _get_expiry_path(project_name: str) -> Path:
    return get_project_dir(project_name) / _EXPIRY_FILE


def _load_expiry(project_name: str) -> Dict[str, float]:
    path = _get_expiry_path(project_name)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_expiry(project_name: str, data: Dict[str, float]) -> None:
    path = _get_expiry_path(project_name)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def set_expiry(project_name: str, key: str, ttl_seconds: int) -> float:
    """Set a TTL (seconds from now) on a secret key. Returns the expiry timestamp."""
    keys = list_secrets(project_name)
    if key not in keys:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive integer.")
    expires_at = time.time() + ttl_seconds
    data = _load_expiry(project_name)
    data[key] = expires_at
    _save_expiry(project_name, data)
    return expires_at


def clear_expiry(project_name: str, key: str) -> None:
    """Remove expiry from a secret key."""
    data = _load_expiry(project_name)
    data.pop(key, None)
    _save_expiry(project_name, data)


def get_expiry(project_name: str, key: str) -> Optional[float]:
    """Return the expiry timestamp for a key, or None if not set."""
    return _load_expiry(project_name).get(key)


def is_expired(project_name: str, key: str) -> bool:
    """Return True if the secret has passed its expiry time."""
    expires_at = get_expiry(project_name, key)
    if expires_at is None:
        return False
    return time.time() > expires_at


def list_expired(project_name: str) -> List[str]:
    """Return all keys in the project that have expired."""
    data = _load_expiry(project_name)
    now = time.time()
    return [key for key, ts in data.items() if now > ts]


def list_expiring_soon(project_name: str, within_seconds: int = 86400) -> List[str]:
    """Return keys expiring within the given window (default 24 h)."""
    data = _load_expiry(project_name)
    now = time.time()
    return [
        key for key, ts in data.items()
        if now <= ts <= now + within_seconds
    ]


def purge_expired(project_name: str) -> List[str]:
    """Remove expiry records for all expired keys and return the purged key names.

    This does not delete the secrets themselves — it only cleans up stale
    entries from the expiry tracking file.
    """
    data = _load_expiry(project_name)
    now = time.time()
    expired_keys = [key for key, ts in data.items() if now > ts]
    for key in expired_keys:
        del data[key]
    if expired_keys:
        _save_expiry(project_name, data)
    return expired_keys
