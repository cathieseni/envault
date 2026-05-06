"""Diff two snapshots or a snapshot vs current secrets."""

from __future__ import annotations

import json
from typing import Any

from envault.snapshot import _get_snapshot_dir, list_snapshots
from envault.secrets import list_secrets, get_secret
from envault.storage import get_project_dir


def _load_snapshot_data(project_name: str, filename: str) -> dict[str, str]:
    """Load decrypted secrets from a snapshot file."""
    snapshot_dir = _get_snapshot_dir(project_name)
    path = snapshot_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {filename}")
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("secrets", {})


def _load_current_secrets(project_name: str) -> dict[str, str]:
    """Load all current secrets for a project."""
    keys = list_secrets(project_name)
    return {k: get_secret(project_name, k) for k in keys}


def diff_snapshots(
    project_name: str, snapshot_a: str, snapshot_b: str
) -> dict[str, Any]:
    """Compare two snapshots and return added, removed, and changed keys."""
    data_a = _load_snapshot_data(project_name, snapshot_a)
    data_b = _load_snapshot_data(project_name, snapshot_b)
    return _compute_diff(data_a, data_b)


def diff_snapshot_vs_current(
    project_name: str, snapshot_name: str
) -> dict[str, Any]:
    """Compare a snapshot against the current live secrets."""
    data_a = _load_snapshot_data(project_name, snapshot_name)
    data_b = _load_current_secrets(project_name)
    return _compute_diff(data_a, data_b)


def _compute_diff(
    old: dict[str, str], new: dict[str, str]
) -> dict[str, Any]:
    """Return a structured diff between two secret dicts."""
    old_keys = set(old)
    new_keys = set(new)

    added = {k: new[k] for k in new_keys - old_keys}
    removed = {k: old[k] for k in old_keys - new_keys}
    changed = {
        k: {"old": old[k], "new": new[k]}
        for k in old_keys & new_keys
        if old[k] != new[k]
    }
    unchanged = [k for k in old_keys & new_keys if old[k] == new[k]]

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
