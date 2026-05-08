"""Secret pinning — mark secrets as pinned to prevent rotation or overwrite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.storage import get_project_dir
from envault.project import get_project


def _get_pin_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "pins.json"


def _load_pins(project_name: str) -> List[str]:
    path = _get_pin_path(project_name)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def _save_pins(project_name: str, pins: List[str]) -> None:
    path = _get_pin_path(project_name)
    path.write_text(json.dumps(sorted(set(pins)), indent=2))


def pin_secret(project_name: str, key: str) -> None:
    """Pin a secret key so it cannot be rotated or overwritten."""
    get_project(project_name)  # raises if project missing
    from envault.secrets import list_secrets
    if key not in list_secrets(project_name):
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    pins = _load_pins(project_name)
    if key not in pins:
        pins.append(key)
        _save_pins(project_name, pins)


def unpin_secret(project_name: str, key: str) -> None:
    """Remove pin from a secret key."""
    get_project(project_name)
    pins = _load_pins(project_name)
    if key not in pins:
        raise KeyError(f"Secret '{key}' is not pinned in project '{project_name}'.")
    pins.remove(key)
    _save_pins(project_name, pins)


def is_pinned(project_name: str, key: str) -> bool:
    """Return True if the secret key is currently pinned."""
    return key in _load_pins(project_name)


def list_pinned(project_name: str) -> List[str]:
    """Return all pinned secret keys for a project."""
    get_project(project_name)
    return _load_pins(project_name)


def assert_not_pinned(project_name: str, key: str, action: str = "modify") -> None:
    """Raise RuntimeError if the secret is pinned."""
    if is_pinned(project_name, key):
        raise RuntimeError(
            f"Secret '{key}' is pinned and cannot be {action}d. "
            "Unpin it first with 'envault pin unpin'."
        )
