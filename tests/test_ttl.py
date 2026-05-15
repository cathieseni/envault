"""Tests for envault.ttl — TTL management for secrets."""

from __future__ import annotations

import time
import pytest

from envault.project import register_project
from envault.secrets import set_secret, list_secrets
from envault.ttl import (
    set_ttl,
    get_ttl,
    clear_ttl,
    is_expired,
    get_expired_keys,
    purge_expired,
)


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    set_secret("myapp", "DB_PASS", "secret")
    return "myapp"


def test_set_ttl_returns_future_timestamp(project):
    expires_at = set_ttl(project, "API_KEY", 3600)
    assert expires_at > time.time()


def test_get_ttl_returns_entry(project):
    set_ttl(project, "API_KEY", 60)
    entry = get_ttl(project, "API_KEY")
    assert entry is not None
    assert entry["seconds"] == 60
    assert "expires_at" in entry


def test_get_ttl_returns_none_when_not_set(project):
    assert get_ttl(project, "DB_PASS") is None


def test_set_ttl_missing_key_raises(project):
    with pytest.raises(KeyError):
        set_ttl(project, "NONEXISTENT", 60)


def test_set_ttl_zero_seconds_raises(project):
    with pytest.raises(ValueError):
        set_ttl(project, "API_KEY", 0)


def test_set_ttl_negative_raises(project):
    with pytest.raises(ValueError):
        set_ttl(project, "API_KEY", -10)


def test_clear_ttl_removes_entry(project):
    set_ttl(project, "API_KEY", 60)
    removed = clear_ttl(project, "API_KEY")
    assert removed is True
    assert get_ttl(project, "API_KEY") is None


def test_clear_ttl_returns_false_if_not_set(project):
    assert clear_ttl(project, "DB_PASS") is False


def test_is_expired_false_for_future_ttl(project):
    set_ttl(project, "API_KEY", 3600)
    assert is_expired(project, "API_KEY") is False


def test_is_expired_false_when_no_ttl(project):
    assert is_expired(project, "DB_PASS") is False


def test_is_expired_true_for_past_expiry(project, monkeypatch):
    set_ttl(project, "API_KEY", 3600)
    # Simulate time having passed beyond TTL
    monkeypatch.setattr("envault.ttl.time.time", lambda: time.time() + 7200)
    assert is_expired(project, "API_KEY") is True


def test_get_expired_keys_returns_elapsed(project, monkeypatch):
    set_ttl(project, "API_KEY", 3600)
    set_ttl(project, "DB_PASS", 7200)
    monkeypatch.setattr("envault.ttl.time.time", lambda: time.time() + 10000)
    expired = get_expired_keys(project)
    assert "API_KEY" in expired
    assert "DB_PASS" in expired


def test_purge_expired_deletes_secrets(project, monkeypatch):
    set_ttl(project, "API_KEY", 3600)
    monkeypatch.setattr("envault.ttl.time.time", lambda: time.time() + 7200)
    purged = purge_expired(project)
    assert "API_KEY" in purged
    assert "API_KEY" not in list_secrets(project)
    assert get_ttl(project, "API_KEY") is None
