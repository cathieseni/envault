"""Secret policy enforcement: define and validate rules per project."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envault.storage import get_project_dir, load_secrets

_DEFAULTS: dict[str, Any] = {
    "min_length": 8,
    "max_length": 512,
    "require_uppercase": False,
    "require_digit": False,
    "require_special": False,
    "disallow_keys": [],
}


def _get_policy_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "policy.json"


def _load_policy(project_name: str) -> dict[str, Any]:
    path = _get_policy_path(project_name)
    if not path.exists():
        return dict(_DEFAULTS)
    with path.open() as f:
        data = json.load(f)
    return {**_DEFAULTS, **data}


def _save_policy(project_name: str, policy: dict[str, Any]) -> None:
    path = _get_policy_path(project_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(policy, f, indent=2)


def set_policy(project_name: str, **kwargs: Any) -> dict[str, Any]:
    """Update policy fields for a project. Unknown keys are ignored."""
    policy = _load_policy(project_name)
    for key, value in kwargs.items():
        if key in _DEFAULTS:
            policy[key] = value
    _save_policy(project_name, policy)
    return policy


def get_policy(project_name: str) -> dict[str, Any]:
    """Return the effective policy for a project."""
    return _load_policy(project_name)


def reset_policy(project_name: str) -> None:
    """Remove any custom policy, reverting to defaults."""
    path = _get_policy_path(project_name)
    if path.exists():
        path.unlink()


class PolicyViolation(Exception):
    pass


def validate_value(project_name: str, key: str, value: str) -> None:
    """Raise PolicyViolation if *value* for *key* breaks the project policy."""
    policy = _load_policy(project_name)

    if key in policy["disallow_keys"]:
        raise PolicyViolation(f"Key '{key}' is disallowed by policy.")

    length = len(value)
    if length < policy["min_length"]:
        raise PolicyViolation(
            f"Value for '{key}' is too short ({length} < {policy['min_length']})."
        )
    if length > policy["max_length"]:
        raise PolicyViolation(
            f"Value for '{key}' is too long ({length} > {policy['max_length']})."
        )
    if policy["require_uppercase"] and not any(c.isupper() for c in value):
        raise PolicyViolation(f"Value for '{key}' must contain an uppercase letter.")
    if policy["require_digit"] and not any(c.isdigit() for c in value):
        raise PolicyViolation(f"Value for '{key}' must contain a digit.")
    if policy["require_special"] and not any(
        c in "!@#$%^&*()-_=+[]{}|;:',.<>?/`~" for c in value
    ):
        raise PolicyViolation(f"Value for '{key}' must contain a special character.")


def audit_project(project_name: str) -> list[str]:
    """Validate all current secrets against the project policy.

    Returns a list of violation messages (empty if all pass).
    """
    secrets = load_secrets(project_name)
    violations: list[str] = []
    for key, value in secrets.items():
        try:
            validate_value(project_name, key, value)
        except PolicyViolation as exc:
            violations.append(str(exc))
    return violations
