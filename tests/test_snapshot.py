"""Tests for envault.snapshot."""

import os
import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.snapshot import (
    create_snapshot,
    list_snapshots,
    restore_snapshot,
    delete_snapshot,
    _get_snapshot_dir,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("snaptest")
    return "snaptest"


def test_create_snapshot_returns_filename(project):
    set_secret(project, "KEY", "value")
    filename = create_snapshot(project)
    assert filename.endswith(".json")


def test_create_snapshot_with_label(project):
    filename = create_snapshot(project, label="before-deploy")
    assert "before-deploy" in filename


def test_snapshot_file_exists_on_disk(project):
    set_secret(project, "A", "1")
    filename = create_snapshot(project)
    snap_dir = _get_snapshot_dir(project)
    assert os.path.exists(os.path.join(snap_dir, filename))


def test_list_snapshots_empty(project):
    assert list_snapshots(project) == []


def test_list_snapshots_returns_metadata(project):
    set_secret(project, "X", "y")
    create_snapshot(project, label="v1")
    create_snapshot(project, label="v2")
    snaps = list_snapshots(project)
    assert len(snaps) == 2
    assert snaps[0]["label"] == "v1"
    assert snaps[1]["label"] == "v2"
    assert snaps[0]["secret_count"] == 1


def test_restore_snapshot_overwrites_secrets(project):
    set_secret(project, "DB", "original")
    filename = create_snapshot(project)
    set_secret(project, "DB", "changed")
    set_secret(project, "EXTRA", "extra")
    count = restore_snapshot(project, filename)
    assert count == 1  # only DB was in the snapshot


def test_restore_missing_snapshot_raises(project):
    with pytest.raises(FileNotFoundError):
        restore_snapshot(project, "nonexistent.json")


def test_delete_snapshot(project):
    filename = create_snapshot(project)
    delete_snapshot(project, filename)
    assert list_snapshots(project) == []


def test_delete_missing_snapshot_raises(project):
    with pytest.raises(FileNotFoundError):
        delete_snapshot(project, "ghost.json")
