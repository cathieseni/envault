"""Replay audit log events to reconstruct secret state at a given point in time."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.audit import get_audit_log
from envault.project import get_project


@dataclass
class ReplayResult:
    project: str
    as_of: datetime.datetime
    secrets: Dict[str, str] = field(default_factory=dict)
    events_applied: int = 0

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ReplayResult(project={self.project!r}, as_of={self.as_of.isoformat()}, "
            f"keys={list(self.secrets.keys())}, events_applied={self.events_applied})"
        )


def replay_project(
    project_name: str,
    as_of: Optional[datetime.datetime] = None,
) -> ReplayResult:
    """Reconstruct the secret state of *project_name* up to *as_of*.

    Only SET and DELETE audit events are replayed.  If *as_of* is None the
    entire log is replayed (i.e. current state according to the audit log).

    Returns a :class:`ReplayResult` with the reconstructed mapping.
    """
    get_project(project_name)  # raises KeyError if unknown

    if as_of is None:
        as_of = datetime.datetime.now(tz=datetime.timezone.utc)

    # Normalise to UTC-aware datetime for comparison
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=datetime.timezone.utc)

    log = get_audit_log(project_name)
    secrets: Dict[str, str] = {}
    events_applied = 0

    for entry in log:
        ts_str = entry.get("timestamp", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            continue

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=datetime.timezone.utc)

        if ts > as_of:
            break

        action = entry.get("action", "")
        key = entry.get("key", "")
        if not key:
            continue

        if action == "set":
            value = entry.get("value", "")
            secrets[key] = value
            events_applied += 1
        elif action == "delete":
            secrets.pop(key, None)
            events_applied += 1

    return ReplayResult(
        project=project_name,
        as_of=as_of,
        secrets=secrets,
        events_applied=events_applied,
    )


def replay_key(
    project_name: str,
    key: str,
    as_of: Optional[datetime.datetime] = None,
) -> List[Dict]:
    """Return all audit events for *key* in *project_name* up to *as_of*."""
    get_project(project_name)

    if as_of is None:
        as_of = datetime.datetime.now(tz=datetime.timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=datetime.timezone.utc)

    log = get_audit_log(project_name)
    events: List[Dict] = []

    for entry in log:
        ts_str = entry.get("timestamp", "")
        try:
            ts = datetime.datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=datetime.timezone.utc)
        if ts > as_of:
            break
        if entry.get("key") == key:
            events.append(entry)

    return events
