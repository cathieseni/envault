"""Secret value signing — HMAC-based signatures for tamper detection."""

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir, load_secrets

_SIG_FILE = "signatures.json"
_HMAC_KEY_FILE = "sig.key"


def _get_sig_path(project: str) -> Path:
    return get_project_dir(project) / _SIG_FILE


def _get_or_create_hmac_key(project: str) -> bytes:
    key_path = get_project_dir(project) / _HMAC_KEY_FILE
    if key_path.exists():
        return key_path.read_bytes()
    key = os.urandom(32)
    key_path.write_bytes(key)
    return key


def _load_signatures(project: str) -> dict:
    path = _get_sig_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_signatures(project: str, data: dict) -> None:
    _get_sig_path(project).write_text(json.dumps(data, indent=2))


def _compute_hmac(key: bytes, value: str) -> str:
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def sign_secret(project: str, secret_key: str) -> str:
    """Compute and store an HMAC signature for the current value of a secret."""
    secrets = load_secrets(project)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' not found in project '{project}'")
    key = _get_or_create_hmac_key(project)
    sig = _compute_hmac(key, secrets[secret_key])
    sigs = _load_signatures(project)
    sigs[secret_key] = sig
    _save_signatures(project, sigs)
    return sig


def verify_secret(project: str, secret_key: str) -> bool:
    """Return True if the current secret value matches its stored signature."""
    secrets = load_secrets(project)
    if secret_key not in secrets:
        raise KeyError(f"Secret '{secret_key}' not found in project '{project}'")
    sigs = _load_signatures(project)
    if secret_key not in sigs:
        return False
    key = _get_or_create_hmac_key(project)
    expected = _compute_hmac(key, secrets[secret_key])
    return hmac.compare_digest(expected, sigs[secret_key])


def get_signature(project: str, secret_key: str) -> Optional[str]:
    """Return the stored signature for a key, or None if not signed."""
    return _load_signatures(project).get(secret_key)


def remove_signature(project: str, secret_key: str) -> None:
    """Remove the stored signature for a key."""
    sigs = _load_signatures(project)
    if secret_key not in sigs:
        raise KeyError(f"No signature found for '{secret_key}' in project '{project}'")
    del sigs[secret_key]
    _save_signatures(project, sigs)


def list_signatures(project: str) -> dict:
    """Return all stored signatures for a project."""
    return dict(_load_signatures(project))
