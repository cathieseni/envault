"""Webhook notification support for envault events."""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

from envault.storage import get_project_dir


def _get_webhook_path(project: str) -> Path:
    return get_project_dir(project) / "webhooks.json"


def _load_webhooks(project: str) -> dict[str, Any]:
    path = _get_webhook_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_webhooks(project: str, data: dict[str, Any]) -> None:
    _get_webhook_path(project).write_text(json.dumps(data, indent=2))


def add_webhook(project: str, name: str, url: str, events: list[str] | None = None) -> None:
    """Register a webhook URL under *name* for *project*.

    *events* is an optional list of event names to filter on (e.g.
    ``['set', 'delete', 'rotate']``).  Pass ``None`` or an empty list to
    receive all events.
    """
    data = _load_webhooks(project)
    data[name] = {"url": url, "events": events or []}
    _save_webhooks(project, data)


def remove_webhook(project: str, name: str) -> None:
    """Remove a registered webhook by *name*."""
    data = _load_webhooks(project)
    if name not in data:
        raise KeyError(f"Webhook '{name}' not found in project '{project}'")
    del data[name]
    _save_webhooks(project, data)


def list_webhooks(project: str) -> dict[str, Any]:
    """Return all registered webhooks for *project*."""
    return _load_webhooks(project)


def fire_event(project: str, event: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Send *payload* to every webhook registered for *event* in *project*.

    Returns a list of result dicts with keys ``name``, ``url``, ``status``
    and optionally ``error``.
    """
    data = _load_webhooks(project)
    results: list[dict[str, Any]] = []
    body = json.dumps({"project": project, "event": event, "ts": time.time(), **payload}).encode()

    for name, cfg in data.items():
        allowed = cfg.get("events", [])
        if allowed and event not in allowed:
            continue
        req = urllib.request.Request(
            cfg["url"],
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                results.append({"name": name, "url": cfg["url"], "status": resp.status})
        except urllib.error.URLError as exc:
            results.append({"name": name, "url": cfg["url"], "status": None, "error": str(exc)})
    return results
