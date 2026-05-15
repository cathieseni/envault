"""Tests for envault.archive."""

from __future__ import annotations

import time
import pytest

from envault import storage
from envault.project import register_project
from envault.secrets import set_secret
from envault.archive import (
    archive_project,
    delete_archived,
    list_archived,
    restore_project,
)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_VAULT_DIR", tmp_path / ".envault")
    yield


@pytest.fixture
def project():
    register_project("myapp")
    set_secret("myapp", "API_KEY", "supersecret")
    return "myapp"


def test_archive_removes_from_active_projects(project):
    archive_project("myapp")
    projects = storage.load_projects()
    assert "myapp" not in projects


def test_archive_creates_archive_entry(project):
    archive_project("myapp")
    entries = list_archived()
    assert len(entries) == 1
    assert entries[0]["name"] == "myapp"


def test_archive_missing_project_raises():
    with pytest.raises(KeyError):
        archive_project("nonexistent")


def test_list_archived_empty_initially():
    assert list_archived() == []


def test_restore_brings_project_back(project):
    archive_project("myapp")
    entries = list_archived()
    assert len(entries) == 1

    restored_name = restore_project(entries[0]["archive_name"])
    assert restored_name == "myapp"

    projects = storage.load_projects()
    assert "myapp" in projects


def test_restore_removes_from_archive(project):
    archive_project("myapp")
    entries = list_archived()
    restore_project(entries[0]["archive_name"])
    assert list_archived() == []


def test_restore_without_overwrite_raises_if_project_exists(project):
    archive_project("myapp")
    entries = list_archived()
    archive_name = entries[0]["archive_name"]

    # Re-register the project so it exists again
    register_project("myapp")

    with pytest.raises(ValueError, match="already exists"):
        restore_project(archive_name, overwrite=False)


def test_restore_with_overwrite_succeeds(project):
    archive_project("myapp")
    entries = list_archived()
    archive_name = entries[0]["archive_name"]

    register_project("myapp")
    restored = restore_project(archive_name, overwrite=True)
    assert restored == "myapp"


def test_delete_archived_removes_permanently(project):
    archive_project("myapp")
    entries = list_archived()
    delete_archived(entries[0]["archive_name"])
    assert list_archived() == []


def test_delete_archived_missing_raises():
    with pytest.raises(FileNotFoundError):
        delete_archived("myapp__9999999999")


def test_archive_entry_has_valid_timestamp(project):
    before = int(time.time())
    archive_project("myapp")
    after = int(time.time())
    entries = list_archived()
    ts = entries[0]["timestamp"]
    assert before <= ts <= after
