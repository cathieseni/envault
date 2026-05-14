"""Tests for envault.history module."""

import os
import pytest

from envault.history import record_change, get_history, clear_history, all_history
from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_PASS", "initial")
    return "myapp"


def test_record_and_get_history(project):
    record_change(project, "DB_PASS", "initial", "updated", actor="test")
    entries = get_history(project, "DB_PASS")
    assert len(entries) == 1
    assert entries[0]["old_value"] == "initial"
    assert entries[0]["new_value"] == "updated"
    assert entries[0]["actor"] == "test"


def test_history_missing_key_raises(project):
    with pytest.raises(KeyError):
        get_history(project, "NONEXISTENT")


def test_multiple_entries_ordered(project):
    record_change(project, "DB_PASS", "v1", "v2")
    record_change(project, "DB_PASS", "v2", "v3")
    entries = get_history(project, "DB_PASS")
    assert len(entries) == 2
    assert entries[0]["new_value"] == "v2"
    assert entries[1]["new_value"] == "v3"


def test_clear_history_removes_entries(project):
    record_change(project, "DB_PASS", "old", "new")
    clear_history(project, "DB_PASS")
    with pytest.raises(KeyError):
        get_history(project, "DB_PASS")


def test_clear_history_nonexistent_key_is_noop(project):
    clear_history(project, "GHOST_KEY")  # should not raise


def test_all_history_returns_all_keys(project):
    record_change(project, "DB_PASS", "a", "b")
    set_secret(project, "API_KEY", "secret")
    record_change(project, "API_KEY", "old", "new")
    data = all_history(project)
    assert "DB_PASS" in data
    assert "API_KEY" in data


def test_all_history_empty_project(project):
    data = all_history(project)
    assert data == {}


def test_history_capped_at_max(project, monkeypatch):
    import envault.history as h_mod
    monkeypatch.setattr(h_mod, "MAX_HISTORY", 5)
    for i in range(10):
        record_change(project, "DB_PASS", str(i), str(i + 1))
    entries = get_history(project, "DB_PASS")
    assert len(entries) == 5
    assert entries[-1]["new_value"] == "10"


def test_record_default_actor(project):
    record_change(project, "DB_PASS", "x", "y")
    entries = get_history(project, "DB_PASS")
    assert entries[0]["actor"] == "cli"
