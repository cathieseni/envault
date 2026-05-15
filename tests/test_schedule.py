"""Tests for envault.schedule — per-secret rotation scheduling."""

import time
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.schedule import (
    set_schedule,
    get_schedule,
    clear_schedule,
    list_scheduled,
    due_keys,
    mark_rotated,
)


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    set_secret("myapp", "DB_PASS", "secret")
    return "myapp"


def test_set_schedule_stores_entry(project):
    entry = set_schedule(project, "API_KEY", 3600)
    assert entry["interval_seconds"] == 3600
    assert entry["next_rotation"] > time.time()


def test_get_schedule_returns_entry(project):
    set_schedule(project, "API_KEY", 7200)
    entry = get_schedule(project, "API_KEY")
    assert entry is not None
    assert entry["interval_seconds"] == 7200


def test_get_schedule_returns_none_when_not_set(project):
    result = get_schedule(project, "DB_PASS")
    assert result is None


def test_set_schedule_missing_key_raises(project):
    with pytest.raises(KeyError):
        set_schedule(project, "NONEXISTENT", 3600)


def test_set_schedule_zero_interval_raises(project):
    with pytest.raises(ValueError):
        set_schedule(project, "API_KEY", 0)


def test_set_schedule_negative_interval_raises(project):
    with pytest.raises(ValueError):
        set_schedule(project, "API_KEY", -100)


def test_clear_schedule_removes_entry(project):
    set_schedule(project, "API_KEY", 3600)
    clear_schedule(project, "API_KEY")
    assert get_schedule(project, "API_KEY") is None


def test_clear_schedule_missing_key_raises(project):
    with pytest.raises(KeyError):
        clear_schedule(project, "API_KEY")


def test_list_scheduled_returns_all(project):
    set_schedule(project, "API_KEY", 3600)
    set_schedule(project, "DB_PASS", 86400)
    scheduled = list_scheduled(project)
    assert "API_KEY" in scheduled
    assert "DB_PASS" in scheduled


def test_due_keys_returns_overdue(project):
    set_schedule(project, "API_KEY", 3600)
    # Manually backdate next_rotation
    from envault.schedule import _load_schedule, _save_schedule
    data = _load_schedule(project)
    data["API_KEY"]["next_rotation"] = time.time() - 1
    _save_schedule(project, data)
    assert "API_KEY" in due_keys(project)


def test_due_keys_excludes_future(project):
    set_schedule(project, "API_KEY", 9999)
    assert "API_KEY" not in due_keys(project)


def test_mark_rotated_advances_next_rotation(project):
    set_schedule(project, "API_KEY", 3600)
    before = time.time()
    mark_rotated(project, "API_KEY")
    entry = get_schedule(project, "API_KEY")
    assert entry["last_rotated"] >= before
    assert entry["next_rotation"] >= before + 3600


def test_mark_rotated_missing_schedule_raises(project):
    with pytest.raises(KeyError):
        mark_rotated(project, "DB_PASS")
