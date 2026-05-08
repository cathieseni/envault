"""Tests for envault.pin secret pinning module."""

from __future__ import annotations

import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.pin import (
    pin_secret,
    unpin_secret,
    is_pinned,
    list_pinned,
    assert_not_pinned,
)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def project():
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    set_secret("myapp", "DB_PASS", "secret")
    return "myapp"


def test_pin_stores_key(project):
    pin_secret(project, "API_KEY")
    assert "API_KEY" in list_pinned(project)


def test_pin_idempotent(project):
    pin_secret(project, "API_KEY")
    pin_secret(project, "API_KEY")  # should not raise
    assert list_pinned(project).count("API_KEY") == 1


def test_pin_missing_key_raises(project):
    with pytest.raises(KeyError):
        pin_secret(project, "NONEXISTENT")


def test_is_pinned_false_initially(project):
    assert is_pinned(project, "API_KEY") is False


def test_is_pinned_true_after_pin(project):
    pin_secret(project, "API_KEY")
    assert is_pinned(project, "API_KEY") is True


def test_unpin_removes_pin(project):
    pin_secret(project, "API_KEY")
    unpin_secret(project, "API_KEY")
    assert is_pinned(project, "API_KEY") is False


def test_unpin_not_pinned_raises(project):
    with pytest.raises(KeyError):
        unpin_secret(project, "API_KEY")


def test_list_pinned_multiple(project):
    pin_secret(project, "API_KEY")
    pin_secret(project, "DB_PASS")
    pins = list_pinned(project)
    assert "API_KEY" in pins
    assert "DB_PASS" in pins


def test_list_pinned_empty(project):
    assert list_pinned(project) == []


def test_assert_not_pinned_passes_when_unpinned(project):
    assert_not_pinned(project, "API_KEY", "rotate")  # should not raise


def test_assert_not_pinned_raises_when_pinned(project):
    pin_secret(project, "API_KEY")
    with pytest.raises(RuntimeError, match="pinned"):
        assert_not_pinned(project, "API_KEY", "rotate")


def test_pin_missing_project_raises():
    with pytest.raises((KeyError, ValueError)):
        pin_secret("ghost_project", "SOME_KEY")
