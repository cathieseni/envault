"""Tests for envault.retention."""

from __future__ import annotations

import time
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.retention import (
    apply_retention,
    clear_retention,
    get_retention,
    set_retention,
)
from envault.history import record_change


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp", path="/tmp/myapp")
    return "myapp"


def test_get_retention_returns_none_when_not_set(project):
    assert get_retention(project) is None


def test_set_and_get_retention(project):
    set_retention(project, 30)
    assert get_retention(project) == 30


def test_set_retention_zero_raises(project):
    with pytest.raises(ValueError):
        set_retention(project, 0)


def test_set_retention_negative_raises(project):
    with pytest.raises(ValueError):
        set_retention(project, -5)


def test_clear_retention_removes_policy(project):
    set_retention(project, 10)
    clear_retention(project)
    assert get_retention(project) is None


def test_clear_retention_noop_when_not_set(project):
    # Should not raise even if no policy exists
    clear_retention(project)
    assert get_retention(project) is None


def test_apply_retention_no_policy_returns_empty(project):
    set_secret(project, "KEY", "value")
    result = apply_retention(project)
    assert result == []


def test_apply_retention_purges_old_secrets(project):
    set_secret(project, "OLD_KEY", "stale")
    # Manually record a very old history entry
    old_ts = time.time() - (40 * 86400)  # 40 days ago
    record_change(project, "OLD_KEY", "set", {"timestamp": old_ts})

    set_retention(project, 30)
    purged = apply_retention(project)
    assert "OLD_KEY" in purged


def test_apply_retention_keeps_recent_secrets(project):
    set_secret(project, "NEW_KEY", "fresh")
    record_change(project, "NEW_KEY", "set", {"timestamp": time.time()})

    set_retention(project, 30)
    purged = apply_retention(project)
    assert "NEW_KEY" not in purged


def test_apply_retention_returns_list_of_purged_keys(project):
    for key in ("A", "B", "C"):
        set_secret(project, key, "v")
        old_ts = time.time() - (60 * 86400)
        record_change(project, key, "set", {"timestamp": old_ts})

    set_retention(project, 30)
    purged = apply_retention(project)
    assert set(purged) == {"A", "B", "C"}
