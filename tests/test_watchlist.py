"""Tests for envault.watchlist."""

import time
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.watchlist import (
    watch_secret,
    unwatch_secret,
    list_watched,
    is_watched,
    stale_secrets,
    refresh_watch,
    _load_watchlist,
)


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "supersecret")
    set_secret("myapp", "DB_PASS", "dbpassword")
    return "myapp"


def test_watch_secret_stores_entry(project):
    watch_secret(project, "API_KEY", max_age_days=7)
    assert is_watched(project, "API_KEY")


def test_watch_secret_default_max_age(project):
    watch_secret(project, "API_KEY")
    data = _load_watchlist(project)
    assert data["API_KEY"]["max_age_days"] == 30.0


def test_watch_secret_missing_key_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        watch_secret(project, "MISSING")


def test_watch_idempotent_updates_max_age(project):
    watch_secret(project, "API_KEY", max_age_days=10)
    watch_secret(project, "API_KEY", max_age_days=20)
    data = _load_watchlist(project)
    assert data["API_KEY"]["max_age_days"] == 20


def test_unwatch_removes_entry(project):
    watch_secret(project, "API_KEY")
    unwatch_secret(project, "API_KEY")
    assert not is_watched(project, "API_KEY")


def test_unwatch_missing_raises(project):
    with pytest.raises(KeyError):
        unwatch_secret(project, "API_KEY")


def test_list_watched_returns_all(project):
    watch_secret(project, "API_KEY")
    watch_secret(project, "DB_PASS")
    watched = list_watched(project)
    assert set(watched) == {"API_KEY", "DB_PASS"}


def test_is_watched_false_initially(project):
    assert not is_watched(project, "API_KEY")


def test_stale_secrets_empty_when_fresh(project):
    watch_secret(project, "API_KEY", max_age_days=30)
    assert stale_secrets(project) == []


def test_stale_secrets_detects_old_entry(project):
    watch_secret(project, "API_KEY", max_age_days=0.00001)
    time.sleep(0.01)
    stale = stale_secrets(project)
    assert len(stale) == 1
    assert stale[0]["key"] == "API_KEY"
    assert stale[0]["age_days"] > 0


def test_refresh_watch_resets_timestamp(project):
    watch_secret(project, "API_KEY", max_age_days=0.00001)
    time.sleep(0.01)
    assert len(stale_secrets(project)) == 1
    refresh_watch(project, "API_KEY")
    assert stale_secrets(project) == []


def test_refresh_watch_missing_raises(project):
    with pytest.raises(KeyError):
        refresh_watch(project, "API_KEY")
