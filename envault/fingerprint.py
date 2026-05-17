"""Secret fingerprinting — track canonical identity of a secret value across rotations."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir
from envault.project import get_project


def _get_fingerprint_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "fingerprints.json"


def _load_fingerprints(project_name: str) -> dict:
    path = _get_fingerprint_path(project_name)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_fingerprints(project_name: str, data: dict) -> None:
    path = _get_fingerprint_path(project_name)
    path.write_text(json.dumps(data, indent=2))


def _hash_value(value: str) -> str:
    """Return a short SHA-256 fingerprint of the given value."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def record_fingerprint(project_name: str, key: str, value: str) -> str:
    """Record the fingerprint of *value* for *key*. Returns the fingerprint hex."""
    get_project(project_name)  # raises if project unknown
    fp = _hash_value(value)
    data = _load_fingerprints(project_name)
    data[key] = fp
    _save_fingerprints(project_name, data)
    return fp


def get_fingerprint(project_name: str, key: str) -> Optional[str]:
    """Return the stored fingerprint for *key*, or None if not recorded."""
    get_project(project_name)
    return _load_fingerprints(project_name).get(key)


def verify_fingerprint(project_name: str, key: str, value: str) -> bool:
    """Return True if *value* matches the stored fingerprint for *key*."""
    stored = get_fingerprint(project_name, key)
    if stored is None:
        return False
    return stored == _hash_value(value)


def delete_fingerprint(project_name: str, key: str) -> bool:
    """Remove the fingerprint entry for *key*. Returns True if it existed."""
    get_project(project_name)
    data = _load_fingerprints(project_name)
    if key not in data:
        return False
    del data[key]
    _save_fingerprints(project_name, data)
    return True


def list_fingerprints(project_name: str) -> dict:
    """Return a mapping of key -> fingerprint for the project."""
    get_project(project_name)
    return dict(_load_fingerprints(project_name))
