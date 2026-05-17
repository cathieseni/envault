"""Baseline snapshot management: capture and compare a project's 'known good' state."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets, get_secret


def _get_baseline_path(project: str) -> Path:
    return get_project_dir(project) / "baseline.json"


def capture_baseline(project: str) -> dict:
    """Capture the current secrets as the baseline for a project."""
    keys = list_secrets(project)
    data = {k: get_secret(project, k) for k in keys}
    entry = {"captured_at": time.time(), "secrets": data}
    _get_baseline_path(project).write_text(json.dumps(entry, indent=2))
    return entry


def get_baseline(project: str) -> Optional[dict]:
    """Return the stored baseline entry, or None if not set."""
    path = _get_baseline_path(project)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def clear_baseline(project: str) -> bool:
    """Delete the baseline file. Returns True if it existed."""
    path = _get_baseline_path(project)
    if path.exists():
        path.unlink()
        return True
    return False


def diff_from_baseline(project: str) -> dict:
    """Compare current secrets against the baseline.

    Returns a dict with keys:
        added   – keys present now but not in baseline
        removed – keys in baseline but not now
        changed – keys whose values differ
        unchanged – keys that are identical
    """
    baseline = get_baseline(project)
    if baseline is None:
        raise KeyError(f"No baseline captured for project '{project}'.")

    base_secrets: dict = baseline["secrets"]
    current_keys = list_secrets(project)
    current_secrets = {k: get_secret(project, k) for k in current_keys}

    base_set = set(base_secrets)
    curr_set = set(current_secrets)

    added = sorted(curr_set - base_set)
    removed = sorted(base_set - curr_set)
    common = base_set & curr_set
    changed = sorted(k for k in common if base_secrets[k] != current_secrets[k])
    unchanged = sorted(k for k in common if base_secrets[k] == current_secrets[k])

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged": unchanged,
    }
