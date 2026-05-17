"""Tests for envault.lifecycle."""

from __future__ import annotations

import os
import time
import pytest

from envault import storage
from envault.project import register_project
from envault.secrets import set_secret
from envault.lifecycle import (
    record_created,
    record_modified,
    record_accessed,
    get_lifecycle,
    delete_lifecycle,
    list_lifecycle,
)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_VAULT_DIR", str(tmp_path / "vault"))
    yield


@pytest.fixture()
def project():
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    return "myapp"


def test_record_created_returns_timestamp(project):
    ts = record_created(project, "API_KEY")
    assert isinstance(ts, float)
    assert ts <= time.time()


def test_record_created_is_idempotent(project):
    ts1 = record_created(project, "API_KEY")
    time.sleep(0.02)
    ts2 = record_created(project, "API_KEY")
    assert ts1 == ts2, "created_at should not change on second call"


def test_record_modified_updates_timestamp(project):
    ts1 = record_modified(project, "API_KEY")
    time.sleep(0.02)
    ts2 = record_modified(project, "API_KEY")
    assert ts2 > ts1


def test_record_accessed_updates_timestamp(project):
    ts1 = record_accessed(project, "API_KEY")
    time.sleep(0.02)
    ts2 = record_accessed(project, "API_KEY")
    assert ts2 > ts1


def test_get_lifecycle_returns_dict(project):
    record_created(project, "API_KEY")
    record_modified(project, "API_KEY")
    lc = get_lifecycle(project, "API_KEY")
    assert lc is not None
    assert "created_at" in lc
    assert "modified_at" in lc


def test_get_lifecycle_returns_none_for_untracked_key(project):
    lc = get_lifecycle(project, "NONEXISTENT")
    assert lc is None


def test_delete_lifecycle_removes_entry(project):
    record_created(project, "API_KEY")
    removed = delete_lifecycle(project, "API_KEY")
    assert removed is True
    assert get_lifecycle(project, "API_KEY") is None


def test_delete_lifecycle_returns_false_when_not_present(project):
    removed = delete_lifecycle(project, "GHOST_KEY")
    assert removed is False


def test_list_lifecycle_returns_all_tracked(project):
    record_created(project, "API_KEY")
    set_secret(project, "DB_PASS", "secret")
    record_created(project, "DB_PASS")
    all_lc = list_lifecycle(project)
    assert "API_KEY" in all_lc
    assert "DB_PASS" in all_lc


def test_missing_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        record_created("no_such_project", "KEY")
