"""Tests for envault.lock module."""

from __future__ import annotations

import pytest

from envault.lock import (
    lock_secret,
    unlock_secret,
    is_locked,
    list_locked,
    assert_not_locked,
)
from envault.secrets import set_secret
from envault.project import register_project
from envault.storage import get_vault_dir


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project():
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    set_secret("myapp", "DB_PASS", "secret")
    return "myapp"


def test_lock_stores_key(project):
    lock_secret(project, "API_KEY")
    assert "API_KEY" in list_locked(project)


def test_lock_idempotent(project):
    lock_secret(project, "API_KEY")
    lock_secret(project, "API_KEY")  # should not raise or duplicate
    assert list_locked(project).count("API_KEY") == 1


def test_is_locked_false_initially(project):
    assert is_locked(project, "API_KEY") is False


def test_is_locked_true_after_lock(project):
    lock_secret(project, "API_KEY")
    assert is_locked(project, "API_KEY") is True


def test_unlock_removes_key(project):
    lock_secret(project, "API_KEY")
    unlock_secret(project, "API_KEY")
    assert is_locked(project, "API_KEY") is False


def test_unlock_missing_key_raises(project):
    with pytest.raises(KeyError, match="not locked"):
        unlock_secret(project, "API_KEY")


def test_list_locked_multiple(project):
    lock_secret(project, "API_KEY")
    lock_secret(project, "DB_PASS")
    locked = list_locked(project)
    assert set(locked) == {"API_KEY", "DB_PASS"}


def test_list_locked_empty(project):
    assert list_locked(project) == []


def test_assert_not_locked_passes_when_unlocked(project):
    assert_not_locked(project, "API_KEY")  # should not raise


def test_assert_not_locked_raises_when_locked(project):
    lock_secret(project, "API_KEY")
    with pytest.raises(RuntimeError, match="locked"):
        assert_not_locked(project, "API_KEY")


def test_lock_missing_project_raises():
    with pytest.raises(KeyError):
        lock_secret("nonexistent", "KEY")
