"""Tests for envault.trust"""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.trust import (
    VALID_LEVELS,
    get_by_level,
    get_trust,
    list_trust,
    remove_trust,
    set_trust,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "s3cr3t")
    set_secret("myapp", "DB_PASS", "dbpass")
    return "myapp"


def test_set_trust_stores_entry(project):
    entry = set_trust(project, "API_KEY", "trusted")
    assert entry["level"] == "trusted"
    assert "updated_at" in entry


def test_set_trust_with_note(project):
    entry = set_trust(project, "API_KEY", "verified", note="reviewed by alice")
    assert entry["note"] == "reviewed by alice"


def test_set_trust_invalid_level_raises(project):
    with pytest.raises(ValueError, match="Invalid trust level"):
        set_trust(project, "API_KEY", "unknown")


def test_set_trust_missing_key_raises(project):
    with pytest.raises(KeyError):
        set_trust(project, "GHOST_KEY", "trusted")


def test_get_trust_returns_entry(project):
    set_trust(project, "API_KEY", "pending")
    entry = get_trust(project, "API_KEY")
    assert entry is not None
    assert entry["level"] == "pending"


def test_get_trust_returns_none_when_not_set(project):
    assert get_trust(project, "API_KEY") is None


def test_remove_trust_returns_true_when_exists(project):
    set_trust(project, "API_KEY", "trusted")
    result = remove_trust(project, "API_KEY")
    assert result is True
    assert get_trust(project, "API_KEY") is None


def test_remove_trust_returns_false_when_missing(project):
    assert remove_trust(project, "API_KEY") is False


def test_list_trust_returns_all(project):
    set_trust(project, "API_KEY", "trusted")
    set_trust(project, "DB_PASS", "untrusted")
    entries = list_trust(project)
    assert set(entries.keys()) == {"API_KEY", "DB_PASS"}


def test_list_trust_empty_project(project):
    assert list_trust(project) == {}


def test_get_by_level_filters_correctly(project):
    set_trust(project, "API_KEY", "trusted")
    set_trust(project, "DB_PASS", "untrusted")
    trusted = get_by_level(project, "trusted")
    assert "API_KEY" in trusted
    assert "DB_PASS" not in trusted


def test_get_by_level_invalid_raises(project):
    with pytest.raises(ValueError):
        get_by_level(project, "bogus")


def test_set_trust_idempotent_update(project):
    set_trust(project, "API_KEY", "pending")
    set_trust(project, "API_KEY", "verified", note="final")
    entry = get_trust(project, "API_KEY")
    assert entry["level"] == "verified"
    assert entry["note"] == "final"
