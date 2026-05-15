"""Per-project secret quota enforcement."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir, load_secrets

_DEFAULT_QUOTA = 100
_QUOTA_FILENAME = "quota.json"


def _get_quota_path(project_name: str) -> Path:
    return get_project_dir(project_name) / _QUOTA_FILENAME


def _load_quota_data(project_name: str) -> dict:
    path = _get_quota_path(project_name)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_quota_data(project_name: str, data: dict) -> None:
    path = _get_quota_path(project_name)
    path.write_text(json.dumps(data, indent=2))


def set_quota(project_name: str, limit: int) -> None:
    """Set the maximum number of secrets allowed for a project."""
    if limit < 1:
        raise ValueError("Quota limit must be at least 1.")
    data = _load_quota_data(project_name)
    data["limit"] = limit
    _save_quota_data(project_name, data)


def get_quota(project_name: str) -> int:
    """Return the quota limit for a project (default if not set)."""
    data = _load_quota_data(project_name)
    return data.get("limit", _DEFAULT_QUOTA)


def clear_quota(project_name: str) -> None:
    """Remove any custom quota, reverting to the default."""
    path = _get_quota_path(project_name)
    if path.exists():
        path.unlink()


def check_quota(project_name: str) -> tuple[int, int, bool]:
    """Return (current_count, limit, within_quota)."""
    secrets = load_secrets(project_name)
    current = len(secrets)
    limit = get_quota(project_name)
    return current, limit, current < limit


def enforce_quota(project_name: str) -> None:
    """Raise QuotaExceededError if the project is at or over its limit."""
    current, limit, ok = check_quota(project_name)
    if not ok:
        raise QuotaExceededError(
            f"Project '{project_name}' has reached its secret quota "
            f"({current}/{limit})."
        )


class QuotaExceededError(Exception):
    """Raised when a project exceeds its configured secret quota."""
