"""Thin wrappers around secrets.py that enforce lock checks before mutations."""

from __future__ import annotations

from envault.lock import assert_not_locked
from envault import secrets as _secrets


def set_secret(project_name: str, key: str, value: str) -> None:
    """Set a secret, raising RuntimeError if the key is locked."""
    assert_not_locked(project_name, key)
    _secrets.set_secret(project_name, key, value)


def delete_secret(project_name: str, key: str) -> None:
    """Delete a secret, raising RuntimeError if the key is locked."""
    assert_not_locked(project_name, key)
    _secrets.delete_secret(project_name, key)


def get_secret(project_name: str, key: str) -> str:
    """Get a secret value (locks do not block reads)."""
    return _secrets.get_secret(project_name, key)


def list_secrets(project_name: str) -> list:
    """List all secret keys for a project."""
    return _secrets.list_secrets(project_name)


def rotate_secret_guarded(project_name: str, key: str, length: int = 32) -> tuple:
    """Rotate a secret, raising RuntimeError if the key is locked."""
    assert_not_locked(project_name, key)
    from envault.rotation import rotate_secret
    return rotate_secret(project_name, key, length=length)
