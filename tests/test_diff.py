"""Tests for envault.diff module."""

from __future__ import annotations

import json
import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.snapshot import create_snapshot
from envault.diff import (
    diff_snapshots,
    diff_snapshot_vs_current,
    _compute_diff,
)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def project():
    register_project("myapp", "/tmp/myapp")
    return "myapp"


def test_compute_diff_added():
    result = _compute_diff({"A": "1"}, {"A": "1", "B": "2"})
    assert result["added"] == {"B": "2"}
    assert result["removed"] == {}
    assert result["changed"] == {}
    assert "A" in result["unchanged"]


def test_compute_diff_removed():
    result = _compute_diff({"A": "1", "B": "2"}, {"A": "1"})
    assert result["removed"] == {"B": "2"}
    assert result["added"] == {}


def test_compute_diff_changed():
    result = _compute_diff({"A": "old"}, {"A": "new"})
    assert result["changed"] == {"A": {"old": "old", "new": "new"}}
    assert result["unchanged"] == []


def test_compute_diff_unchanged():
    result = _compute_diff({"A": "same"}, {"A": "same"})
    assert "A" in result["unchanged"]
    assert result["changed"] == {}


def test_compute_diff_empty_dicts():
    """Diffing two empty dicts should return all-empty result."""
    result = _compute_diff({}, {})
    assert result["added"] == {}
    assert result["removed"] == {}
    assert result["changed"] == {}
    assert result["unchanged"] == []


def test_compute_diff_both_empty_vs_populated():
    """Diffing an empty old dict against a populated new dict marks all keys as added."""
    result = _compute_diff({}, {"X": "1", "Y": "2"})
    assert result["added"] == {"X": "1", "Y": "2"}
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_diff_snapshots(project):
    set_secret(project, "DB_URL", "postgres://old")
    snap_a = create_snapshot(project)

    set_secret(project, "DB_URL", "postgres://new")
    set_secret(project, "API_KEY", "abc123")
    snap_b = create_snapshot(project)

    result = diff_snapshots(project, snap_a, snap_b)
    assert result["changed"]["DB_URL"]["old"] == "postgres://old"
    assert result["changed"]["DB_URL"]["new"] == "postgres://new"
    assert "API_KEY" in result["added"]


def test_diff_snapshot_vs_current(project):
    set_secret(project, "TOKEN", "initial")
    snap = create_snapshot(project)

    set_secret(project, "TOKEN", "updated")
    set_secret(project, "NEW_KEY", "hello")

    result = diff_snapshot_vs_current(project, snap)
    assert result["changed"]["TOKEN"]["old"] == "initial"
    assert result["changed"]["TOKEN"]["new"] == "updated"
    assert "NEW_KEY" in result["added"]


def test_diff_snapshot_missing_raises(project):
    with pytest.raises(FileNotFoundError):
        diff_snapshots(project, "ghost_a.json", "ghost_b.json")
