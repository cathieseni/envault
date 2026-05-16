"""Notification channels for envault events (e.g. secret rotated, expired, locked)."""

import json
import time
from pathlib import Path
from typing import List, Optional

from envault.storage import get_project_dir

SUPPORTED_CHANNELS = ("email", "slack", "webhook")


def _get_notification_path(project: str) -> Path:
    return get_project_dir(project) / "notifications.json"


def _load_notifications(project: str) -> dict:
    path = _get_notification_path(project)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_notifications(project: str, data: dict) -> None:
    path = _get_notification_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def add_notification(project: str, channel: str, target: str, events: Optional[List[str]] = None) -> dict:
    """Register a notification channel for the project."""
    if channel not in SUPPORTED_CHANNELS:
        raise ValueError(f"Unsupported channel '{channel}'. Choose from: {SUPPORTED_CHANNELS}")
    data = _load_notifications(project)
    entry = {
        "channel": channel,
        "target": target,
        "events": events or ["rotate", "expire", "delete"],
        "created_at": time.time(),
    }
    data[target] = entry
    _save_notifications(project, data)
    return entry


def remove_notification(project: str, target: str) -> None:
    """Remove a notification channel by target identifier."""
    data = _load_notifications(project)
    if target not in data:
        raise KeyError(f"No notification registered for target '{target}' in project '{project}'")
    del data[target]
    _save_notifications(project, data)


def list_notifications(project: str) -> List[dict]:
    """Return all registered notification channels for the project."""
    data = _load_notifications(project)
    return list(data.values())


def get_notification(project: str, target: str) -> dict:
    """Return a single notification entry by target."""
    data = _load_notifications(project)
    if target not in data:
        raise KeyError(f"No notification registered for target '{target}' in project '{project}'")
    return data[target]


def update_events(project: str, target: str, events: List[str]) -> dict:
    """Update the event list for an existing notification channel."""
    data = _load_notifications(project)
    if target not in data:
        raise KeyError(f"No notification registered for target '{target}' in project '{project}'")
    data[target]["events"] = events
    _save_notifications(project, data)
    return data[target]
