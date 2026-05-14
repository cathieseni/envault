"""Hook layer that wraps secrets.py to automatically record history on changes."""

from envault.secrets import get_secret, set_secret as _set_secret, delete_secret as _delete_secret
from envault.history import record_change


def set_secret_with_history(project_name: str, key: str, value: str, actor: str = "cli") -> None:
    """Set a secret and record the old->new transition in history."""
    try:
        old_value = get_secret(project_name, key)
    except KeyError:
        old_value = ""

    _set_secret(project_name, key, value)

    if old_value != value:
        record_change(project_name, key, old_value, value, actor=actor)


def delete_secret_with_history(project_name: str, key: str, actor: str = "cli") -> None:
    """Delete a secret and record the deletion event in history."""
    try:
        old_value = get_secret(project_name, key)
    except KeyError:
        old_value = ""

    _delete_secret(project_name, key)
    record_change(project_name, key, old_value, "<deleted>", actor=actor)
