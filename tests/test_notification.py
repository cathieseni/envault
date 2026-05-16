"""Tests for envault.notification module."""

import pytest

from envault.notification import (
    add_notification,
    remove_notification,
    list_notifications,
    get_notification,
    update_events,
)
from envault.project import register_project
from envault.storage import get_vault_dir

import os


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_add_notification_stores_entry(project):
    entry = add_notification(project, "slack", "https://hooks.slack.com/xxx")
    assert entry["channel"] == "slack"
    assert entry["target"] == "https://hooks.slack.com/xxx"
    assert "rotate" in entry["events"]


def test_add_notification_custom_events(project):
    entry = add_notification(project, "email", "admin@example.com", events=["rotate"])
    assert entry["events"] == ["rotate"]


def test_add_notification_invalid_channel_raises(project):
    with pytest.raises(ValueError, match="Unsupported channel"):
        add_notification(project, "sms", "555-1234")


def test_add_notification_overwrites_same_target(project):
    add_notification(project, "slack", "https://hooks.slack.com/xxx", events=["rotate"])
    add_notification(project, "slack", "https://hooks.slack.com/xxx", events=["expire"])
    entry = get_notification(project, "https://hooks.slack.com/xxx")
    assert entry["events"] == ["expire"]


def test_list_notifications_empty(project):
    assert list_notifications(project) == []


def test_list_notifications_multiple(project):
    add_notification(project, "slack", "https://hooks.slack.com/a")
    add_notification(project, "email", "dev@example.com")
    entries = list_notifications(project)
    assert len(entries) == 2


def test_get_notification_returns_entry(project):
    add_notification(project, "webhook", "https://my.api/hook")
    entry = get_notification(project, "https://my.api/hook")
    assert entry["channel"] == "webhook"


def test_get_notification_missing_raises(project):
    with pytest.raises(KeyError, match="No notification"):
        get_notification(project, "nonexistent")


def test_remove_notification(project):
    add_notification(project, "slack", "https://hooks.slack.com/xxx")
    remove_notification(project, "https://hooks.slack.com/xxx")
    assert list_notifications(project) == []


def test_remove_notification_missing_raises(project):
    with pytest.raises(KeyError, match="No notification"):
        remove_notification(project, "ghost")


def test_update_events(project):
    add_notification(project, "email", "ops@example.com", events=["rotate"])
    updated = update_events(project, "ops@example.com", ["expire", "delete"])
    assert updated["events"] == ["expire", "delete"]


def test_update_events_missing_raises(project):
    with pytest.raises(KeyError, match="No notification"):
        update_events(project, "nobody", ["rotate"])
