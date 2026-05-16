"""Dispatch notifications to registered channels when vault events occur."""

import urllib.request
import urllib.error
import json
import time
from typing import Optional

from envault.notification import list_notifications


def _post_webhook(url: str, payload: dict) -> bool:
    """Send a JSON POST to a webhook URL. Returns True on success."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5):
            return True
    except urllib.error.URLError:
        return False


def _format_payload(project: str, event: str, key: Optional[str], extra: Optional[dict]) -> dict:
    payload = {
        "project": project,
        "event": event,
        "timestamp": time.time(),
    }
    if key:
        payload["key"] = key
    if extra:
        payload.update(extra)
    return payload


def dispatch(project: str, event: str, key: Optional[str] = None, extra: Optional[dict] = None) -> list:
    """Dispatch an event to all matching notification channels for the project.

    Returns a list of dispatch result dicts with 'target', 'channel', 'success'.
    """
    results = []
    notifications = list_notifications(project)
    payload = _format_payload(project, event, key, extra)

    for entry in notifications:
        if event not in entry.get("events", []):
            continue

        channel = entry["channel"]
        target = entry["target"]
        success = False

        if channel in ("webhook", "slack"):
            success = _post_webhook(target, payload)
        elif channel == "email":
            # Email dispatch is a stub — integrate with an SMTP provider externally.
            success = True

        results.append({"target": target, "channel": channel, "success": success})

    return results
