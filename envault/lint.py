"""Lint secrets for common issues: weak values, duplicates, missing keys."""

from __future__ import annotations

from typing import Any

from envault.secrets import list_secrets, get_secret
from envault.project import get_project

_WEAK_VALUES = {"password", "secret", "changeme", "123456", "admin", "test", "example"}
_MIN_LENGTH = 8


def _check_weak_value(key: str, value: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    lower = value.strip().lower()
    if lower in _WEAK_VALUES:
        issues.append({"key": key, "level": "error", "message": f"Value is a known weak/placeholder string."})
    if len(value) < _MIN_LENGTH:
        issues.append({"key": key, "level": "warning", "message": f"Value is shorter than {_MIN_LENGTH} characters."})
    return issues


def _check_duplicate_values(secrets: dict[str, str]) -> list[dict[str, Any]]:
    seen: dict[str, list[str]] = {}
    for key, value in secrets.items():
        seen.setdefault(value, []).append(key)
    issues: list[dict[str, Any]] = []
    for value, keys in seen.items():
        if len(keys) > 1:
            issues.append({
                "key": ", ".join(keys),
                "level": "warning",
                "message": f"Duplicate value shared by keys: {', '.join(keys)}",
            })
    return issues


def _check_empty_values(secrets: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {"key": k, "level": "error", "message": "Value is empty."}
        for k, v in secrets.items()
        if not v.strip()
    ]


def lint_project(project_name: str) -> list[dict[str, Any]]:
    """Run all lint checks on a project's secrets and return a list of issues."""
    get_project(project_name)  # raises if missing
    keys = list_secrets(project_name)
    secrets = {k: get_secret(project_name, k) for k in keys}

    issues: list[dict[str, Any]] = []
    issues.extend(_check_empty_values(secrets))
    issues.extend(_check_duplicate_values(secrets))
    for key, value in secrets.items():
        issues.extend(_check_weak_value(key, value))
    return issues
