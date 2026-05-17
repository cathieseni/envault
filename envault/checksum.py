"""Checksum tracking for secrets — detect out-of-band tampering."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir, load_secrets


def _get_checksum_path(project: str) -> Path:
    return get_project_dir(project) / "checksums.json"


def _load_checksums(project: str) -> dict:
    path = _get_checksum_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_checksums(project: str, data: dict) -> None:
    path = _get_checksum_path(project)
    path.write_text(json.dumps(data, indent=2))


def _hash_value(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def record_checksum(project: str, key: str) -> str:
    """Record a SHA-256 checksum for the current value of *key*.

    Returns the hex digest that was stored.
    Raises KeyError if the key does not exist.
    """
    secrets = load_secrets(project)
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in project '{project}'")
    digest = _hash_value(secrets[key])
    data = _load_checksums(project)
    data[key] = digest
    _save_checksums(project, data)
    return digest


def verify_checksum(project: str, key: str) -> bool:
    """Return True if the current value matches the recorded checksum.

    Returns False if the value has changed or no checksum is on record.
    Raises KeyError if the key does not exist in the vault.
    """
    secrets = load_secrets(project)
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in project '{project}'")
    data = _load_checksums(project)
    if key not in data:
        return False
    return _hash_value(secrets[key]) == data[key]


def get_checksum(project: str, key: str) -> Optional[str]:
    """Return the stored checksum for *key*, or None if not recorded."""
    data = _load_checksums(project)
    return data.get(key)


def clear_checksum(project: str, key: str) -> None:
    """Remove the stored checksum for *key* (no-op if absent)."""
    data = _load_checksums(project)
    data.pop(key, None)
    _save_checksums(project, data)


def audit_all(project: str) -> dict:
    """Return a mapping of key -> 'ok' | 'tampered' | 'untracked' for every
    secret currently in the project.
    """
    secrets = load_secrets(project)
    data = _load_checksums(project)
    result = {}
    for key, value in secrets.items():
        if key not in data:
            result[key] = "untracked"
        elif _hash_value(value) == data[key]:
            result[key] = "ok"
        else:
            result[key] = "tampered"
    return result
