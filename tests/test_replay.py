"""Tests for envault.replay — audit-log-based state reconstruction."""

from __future__ import annotations

import datetime
import os
import pytest

from envault.replay import replay_project, replay_key
from envault.audit import log_event, clear_audit_log
from envault.project import register_project
from envault.storage import get_vault_dir


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def _ts(offset_seconds: int = 0) -> str:
    base = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    return (base + datetime.timedelta(seconds=offset_seconds)).isoformat()


def test_replay_unknown_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        replay_project("ghost")


def test_replay_empty_log_returns_empty_secrets(project):
    result = replay_project(project)
    assert result.secrets == {}
    assert result.events_applied == 0


def test_replay_set_events_build_state(project):
    log_event(project, "set", key="DB_URL", value="postgres://localhost", timestamp=_ts(0))
    log_event(project, "set", key="API_KEY", value="abc123", timestamp=_ts(1))

    result = replay_project(project)
    assert result.secrets["DB_URL"] == "postgres://localhost"
    assert result.secrets["API_KEY"] == "abc123"
    assert result.events_applied == 2


def test_replay_delete_removes_key(project):
    log_event(project, "set", key="TEMP", value="xyz", timestamp=_ts(0))
    log_event(project, "delete", key="TEMP", timestamp=_ts(1))

    result = replay_project(project)
    assert "TEMP" not in result.secrets
    assert result.events_applied == 2


def test_replay_as_of_cuts_off_later_events(project):
    log_event(project, "set", key="FOO", value="first", timestamp=_ts(0))
    log_event(project, "set", key="FOO", value="second", timestamp=_ts(100))

    cutoff = datetime.datetime(2024, 6, 1, 12, 0, 50, tzinfo=datetime.timezone.utc)
    result = replay_project(project, as_of=cutoff)
    assert result.secrets["FOO"] == "first"
    assert result.events_applied == 1


def test_replay_latest_set_wins(project):
    log_event(project, "set", key="X", value="v1", timestamp=_ts(0))
    log_event(project, "set", key="X", value="v2", timestamp=_ts(1))
    log_event(project, "set", key="X", value="v3", timestamp=_ts(2))

    result = replay_project(project)
    assert result.secrets["X"] == "v3"


def test_replay_key_returns_only_matching_events(project):
    log_event(project, "set", key="A", value="1", timestamp=_ts(0))
    log_event(project, "set", key="B", value="2", timestamp=_ts(1))
    log_event(project, "set", key="A", value="3", timestamp=_ts(2))

    events = replay_key(project, "A")
    assert len(events) == 2
    assert all(e["key"] == "A" for e in events)


def test_replay_key_unknown_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        replay_key("no-such", "KEY")


def test_replay_key_as_of_respected(project):
    log_event(project, "set", key="Z", value="old", timestamp=_ts(0))
    log_event(project, "set", key="Z", value="new", timestamp=_ts(200))

    cutoff = datetime.datetime(2024, 6, 1, 12, 1, 0, tzinfo=datetime.timezone.utc)
    events = replay_key(project, "Z", as_of=cutoff)
    assert len(events) == 1
    assert events[0]["value"] == "old"
