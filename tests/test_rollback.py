"""Tests for envault.rollback."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret, list_secrets
from envault.snapshot import create_snapshot
from envault.rollback import rollback, get_latest_snapshot, RollbackResult


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


# ---------------------------------------------------------------------------
# get_latest_snapshot
# ---------------------------------------------------------------------------

def test_get_latest_snapshot_none_when_no_snapshots(project):
    assert get_latest_snapshot(project) is None


def test_get_latest_snapshot_returns_most_recent(project):
    set_secret(project, "KEY", "v1")
    snap1 = create_snapshot(project, label="first")
    set_secret(project, "KEY", "v2")
    snap2 = create_snapshot(project, label="second")
    latest = get_latest_snapshot(project)
    assert latest == snap2


# ---------------------------------------------------------------------------
# rollback
# ---------------------------------------------------------------------------

def test_rollback_restores_secret_values(project):
    set_secret(project, "DB_URL", "postgres://old")
    create_snapshot(project, label="baseline")

    set_secret(project, "DB_URL", "postgres://new")
    assert get_secret(project, "DB_URL") == "postgres://new"

    result = rollback(project, create_backup=False)
    assert get_secret(project, "DB_URL") == "postgres://old"
    assert "DB_URL" in result.keys_restored


def test_rollback_removes_keys_added_after_snapshot(project):
    set_secret(project, "ORIGINAL", "yes")
    snap = create_snapshot(project)

    set_secret(project, "EXTRA_KEY", "surprise")
    assert "EXTRA_KEY" in list_secrets(project)

    result = rollback(project, snapshot_name=snap, create_backup=False)
    assert "EXTRA_KEY" not in list_secrets(project)
    assert "EXTRA_KEY" in result.keys_removed


def test_rollback_creates_backup_snapshot_by_default(project):
    set_secret(project, "X", "1")
    create_snapshot(project)

    result = rollback(project, create_backup=True)
    assert result.backup_snapshot is not None
    # The backup snapshot filename should contain "pre-rollback".
    assert "pre-rollback" in result.backup_snapshot


def test_rollback_no_backup_when_disabled(project):
    set_secret(project, "X", "1")
    create_snapshot(project)

    result = rollback(project, create_backup=False)
    assert result.backup_snapshot is None


def test_rollback_raises_when_no_snapshots(project):
    with pytest.raises(ValueError, match="No snapshots found"):
        rollback(project)


def test_rollback_result_summary_contains_project(project):
    set_secret(project, "K", "v")
    create_snapshot(project)
    result = rollback(project, create_backup=False)
    summary = result.summary()
    assert project in summary
    assert "Keys restored" in summary
