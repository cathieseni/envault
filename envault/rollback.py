"""Rollback support: revert a project's secrets to a previous snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.snapshot import list_snapshots, restore_snapshot, create_snapshot
from envault.secrets import list_secrets, get_secret, set_secret, delete_secret
from envault.audit import log_event


@dataclass
class RollbackResult:
    project: str
    snapshot_name: str
    keys_restored: List[str] = field(default_factory=list)
    keys_removed: List[str] = field(default_factory=list)
    backup_snapshot: Optional[str] = None

    def summary(self) -> str:
        lines = [
            f"Rolled back '{self.project}' to snapshot '{self.snapshot_name}'",
            f"  Backup created: {self.backup_snapshot}",
            f"  Keys restored : {len(self.keys_restored)}",
            f"  Keys removed  : {len(self.keys_removed)}",
        ]
        return "\n".join(lines)


def get_latest_snapshot(project: str) -> Optional[str]:
    """Return the most recent snapshot filename for *project*, or None."""
    snaps = list_snapshots(project)
    if not snaps:
        return None
    # list_snapshots returns entries sorted oldest-first; take the last.
    return snaps[-1]["filename"]


def rollback(
    project: str,
    snapshot_name: Optional[str] = None,
    *,
    create_backup: bool = True,
) -> RollbackResult:
    """Restore *project* secrets to the state captured in *snapshot_name*.

    If *snapshot_name* is None the most recent snapshot is used.
    When *create_backup* is True a snapshot of the current state is taken
    before the rollback so it can be undone.

    Raises
    ------
    ValueError
        If no snapshot is available or the requested snapshot does not exist.
    """
    if snapshot_name is None:
        snapshot_name = get_latest_snapshot(project)
        if snapshot_name is None:
            raise ValueError(f"No snapshots found for project '{project}'.")

    # Optionally back up current state.
    backup_name: Optional[str] = None
    if create_backup:
        backup_name = create_snapshot(project, label="pre-rollback")

    # Capture current keys so we know what to remove afterwards.
    current_keys = set(list_secrets(project))

    # Restore snapshot (overwrites matching keys).
    restored_data: Dict[str, str] = restore_snapshot(project, snapshot_name)
    restored_keys = list(restored_data.keys())

    # Remove keys that exist now but were not in the snapshot.
    removed_keys: List[str] = []
    for key in current_keys - set(restored_keys):
        delete_secret(project, key)
        removed_keys.append(key)

    log_event(
        project,
        "rollback",
        {
            "snapshot": snapshot_name,
            "backup": backup_name,
            "restored": len(restored_keys),
            "removed": len(removed_keys),
        },
    )

    return RollbackResult(
        project=project,
        snapshot_name=snapshot_name,
        keys_restored=restored_keys,
        keys_removed=removed_keys,
        backup_snapshot=backup_name,
    )
