"""Tests for envault.webhook."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.webhook import add_webhook, remove_webhook, list_webhooks, fire_event


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "secret123")
    return "myapp"


def test_add_webhook_stores_entry(project):
    add_webhook(project, "slack", "https://hooks.example.com/slack")
    hooks = list_webhooks(project)
    assert "slack" in hooks
    assert hooks["slack"]["url"] == "https://hooks.example.com/slack"
    assert hooks["slack"]["events"] == []


def test_add_webhook_with_events(project):
    add_webhook(project, "pager", "https://pager.example.com", events=["rotate", "delete"])
    hooks = list_webhooks(project)
    assert hooks["pager"]["events"] == ["rotate", "delete"]


def test_add_webhook_idempotent_overwrite(project):
    add_webhook(project, "slack", "https://v1.example.com")
    add_webhook(project, "slack", "https://v2.example.com")
    hooks = list_webhooks(project)
    assert hooks["slack"]["url"] == "https://v2.example.com"


def test_remove_webhook_deletes_entry(project):
    add_webhook(project, "slack", "https://hooks.example.com/slack")
    remove_webhook(project, "slack")
    hooks = list_webhooks(project)
    assert "slack" not in hooks


def test_remove_missing_webhook_raises(project):
    with pytest.raises(KeyError, match="ghost"):
        remove_webhook(project, "ghost")


def test_list_webhooks_empty(project):
    assert list_webhooks(project) == {}


def test_fire_event_calls_registered_url(project):
    add_webhook(project, "notify", "https://example.com/hook")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        results = fire_event(project, "set", {"key": "API_KEY"})

    assert len(results) == 1
    assert results[0]["status"] == 200
    assert results[0]["name"] == "notify"
    mock_open.assert_called_once()


def test_fire_event_respects_event_filter(project):
    add_webhook(project, "only_rotate", "https://example.com/hook", events=["rotate"])
    results = fire_event(project, "set", {"key": "API_KEY"})
    assert results == []


def test_fire_event_captures_url_error(project):
    import urllib.error
    add_webhook(project, "broken", "https://broken.example.com")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        results = fire_event(project, "set", {"key": "X"})
    assert results[0]["status"] is None
    assert "timeout" in results[0]["error"]
