"""Tests for envault.expiry module."""

from __future__ import annotations

import time
import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.expiry import (
    set_expiry,
    clear_expiry,
    get_expiry,
    is_expired,
    list_expired,
    list_expiring_soon,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "supersecret")
    set_secret("myapp", "DB_PASS", "dbpassword")
    return "myapp"


def test_set_expiry_returns_timestamp(project):
    ts = set_expiry(project, "API_KEY", ttl_seconds=3600)
    assert ts > time.time()
    assert ts <= time.time() + 3601


def test_get_expiry_returns_none_when_not_set(project):
    assert get_expiry(project, "API_KEY") is None


def test_get_expiry_after_set(project):
    set_expiry(project, "API_KEY", ttl_seconds=60)
    ts = get_expiry(project, "API_KEY")
    assert ts is not None
    assert ts > time.time()


def test_set_expiry_missing_key_raises(project):
    with pytest.raises(KeyError):
        set_expiry(project, "NONEXISTENT", ttl_seconds=60)


def test_set_expiry_zero_ttl_raises(project):
    with pytest.raises(ValueError):
        set_expiry(project, "API_KEY", ttl_seconds=0)


def test_is_expired_false_for_future(project):
    set_expiry(project, "API_KEY", ttl_seconds=3600)
    assert is_expired(project, "API_KEY") is False


def test_is_expired_true_for_past(project, monkeypatch):
    set_expiry(project, "API_KEY", ttl_seconds=3600)
    # Simulate time moving forward past expiry
    monkeypatch.setattr("envault.expiry.time.time", lambda: time.time() + 7200)
    assert is_expired(project, "API_KEY") is True


def test_is_expired_false_when_no_expiry(project):
    assert is_expired(project, "API_KEY") is False


def test_clear_expiry_removes_timestamp(project):
    set_expiry(project, "API_KEY", ttl_seconds=60)
    clear_expiry(project, "API_KEY")
    assert get_expiry(project, "API_KEY") is None


def test_list_expired_returns_expired_keys(project, monkeypatch):
    set_expiry(project, "API_KEY", ttl_seconds=3600)
    set_expiry(project, "DB_PASS", ttl_seconds=3600)
    monkeypatch.setattr("envault.expiry.time.time", lambda: time.time() + 7200)
    expired = list_expired(project)
    assert "API_KEY" in expired
    assert "DB_PASS" in expired


def test_list_expired_empty_when_none_expired(project):
    set_expiry(project, "API_KEY", ttl_seconds=3600)
    assert list_expired(project) == []


def test_list_expiring_soon(project):
    set_expiry(project, "API_KEY", ttl_seconds=600)   # 10 min — within 24 h
    set_expiry(project, "DB_PASS", ttl_seconds=90000)  # 25 h — outside window
    soon = list_expiring_soon(project, within_seconds=86400)
    assert "API_KEY" in soon
    assert "DB_PASS" not in soon
