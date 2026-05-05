"""Snapshot module: capture and restore project secret snapshots."""

import json
import os
from datetime import datetime, timezone

from envault.storage import get_project_dir, load_secrets, save_secrets
from envault.audit import log_event


def _get_snapshot_dir(project_name: str) -> str:
    """Return (and create) the snapshots directory for a project."""
    snap_dir = os.path.join(get_project_dir(project_name), "snapshots")
    os.makedirs(snap_dir, exist_ok=True)
    return snap_dir


def create_snapshot(project_name: str, label: str | None = None) -> str:
    """Persist a snapshot of the current secrets and return its filename."""
    secrets = load_secrets(project_name)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{timestamp}.json" if not label else f"{timestamp}_{label}.json"
    snap_path = os.path.join(_get_snapshot_dir(project_name), filename)
    with open(snap_path, "w") as fh:
        json.dump({"timestamp": timestamp, "label": label, "secrets": secrets}, fh, indent=2)
    log_event(project_name, "snapshot_create", {"snapshot": filename})
    return filename


def list_snapshots(project_name: str) -> list[dict]:
    """Return metadata for all snapshots, sorted oldest-first."""
    snap_dir = _get_snapshot_dir(project_name)
    entries = []
    for fname in sorted(os.listdir(snap_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(snap_dir, fname)
        with open(path) as fh:
            data = json.load(fh)
        entries.append({
            "filename": fname,
            "timestamp": data.get("timestamp"),
            "label": data.get("label"),
            "secret_count": len(data.get("secrets", {})),
        })
    return entries


def restore_snapshot(project_name: str, filename: str) -> int:
    """Overwrite current secrets with those from *filename*. Returns secret count."""
    snap_path = os.path.join(_get_snapshot_dir(project_name), filename)
    if not os.path.exists(snap_path):
        raise FileNotFoundError(f"Snapshot '{filename}' not found for project '{project_name}'.")
    with open(snap_path) as fh:
        data = json.load(fh)
    secrets = data.get("secrets", {})
    save_secrets(project_name, secrets)
    log_event(project_name, "snapshot_restore", {"snapshot": filename})
    return len(secrets)


def delete_snapshot(project_name: str, filename: str) -> None:
    """Remove a snapshot file."""
    snap_path = os.path.join(_get_snapshot_dir(project_name), filename)
    if not os.path.exists(snap_path):
        raise FileNotFoundError(f"Snapshot '{filename}' not found for project '{project_name}'.")
    os.remove(snap_path)
    log_event(project_name, "snapshot_delete", {"snapshot": filename})
