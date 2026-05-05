"""Secret rotation logic for envault."""

import secrets as _secrets_mod
import string
from datetime import datetime, timezone

from envault.secrets import get_secret, set_secret, list_secrets
from envault.audit import log_event

DEFAULT_LENGTH = 32
DEFAULT_ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"


def _generate_secret_value(length: int = DEFAULT_LENGTH, alphabet: str = DEFAULT_ALPHABET) -> str:
    """Generate a cryptographically secure random secret value."""
    return "".join(_secrets_mod.choice(alphabet) for _ in range(length))


def rotate_secret(
    project_name: str,
    key: str,
    length: int = DEFAULT_LENGTH,
    alphabet: str = DEFAULT_ALPHABET,
) -> dict:
    """Rotate a single secret for a project.

    Returns a dict with 'key', 'old_value', 'new_value', and 'rotated_at'.
    Raises KeyError if the secret does not exist.
    """
    old_value = get_secret(project_name, key)  # raises KeyError if missing
    new_value = _generate_secret_value(length, alphabet)
    set_secret(project_name, key, new_value)

    rotated_at = datetime.now(timezone.utc).isoformat()
    log_event(
        project_name,
        "rotate",
        {"key": key, "rotated_at": rotated_at},
    )

    return {
        "key": key,
        "old_value": old_value,
        "new_value": new_value,
        "rotated_at": rotated_at,
    }


def rotate_all_secrets(
    project_name: str,
    length: int = DEFAULT_LENGTH,
    alphabet: str = DEFAULT_ALPHABET,
) -> list[dict]:
    """Rotate every secret stored for a project.

    Returns a list of rotation result dicts (same shape as rotate_secret).
    """
    keys = list_secrets(project_name)
    results = []
    for key in keys:
        result = rotate_secret(project_name, key, length=length, alphabet=alphabet)
        results.append(result)
    return results
