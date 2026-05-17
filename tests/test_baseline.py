"""Tests for envault.baseline."""

from __future__ import annotations

import os
import pytest

from envault.baseline import (
    capture_baseline,
    get_baseline,
    clear_baseline,
    diff_from_baseline,
)
from envault.project import register_project
from envault.secrets import set_secret, delete_secret


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_capture_baseline_returns_secrets(project):
    set_secret(project, "KEY1", "val1")
    set_secret(project, "KEY2", "val2")
    entry = capture_baseline(project)
    assert entry["secrets"] == {"KEY1": "val1", "KEY2": "val2"}
    assert "captured_at" in entry


def test_get_baseline_returns_none_when_not_set(project):
    assert get_baseline(project) is None


def test_get_baseline_after_capture(project):
    set_secret(project, "X", "y")
    capture_baseline(project)
    entry = get_baseline(project)
    assert entry is not None
    assert entry["secrets"]["X"] == "y"


def test_clear_baseline_returns_true_when_exists(project):
    set_secret(project, "A", "1")
    capture_baseline(project)
    assert clear_baseline(project) is True
    assert get_baseline(project) is None


def test_clear_baseline_returns_false_when_missing(project):
    assert clear_baseline(project) is False


def test_diff_no_baseline_raises(project):
    with pytest.raises(KeyError, match="No baseline"):
        diff_from_baseline(project)


def test_diff_unchanged(project):
    set_secret(project, "KEY", "value")
    capture_baseline(project)
    result = diff_from_baseline(project)
    assert result["unchanged"] == ["KEY"]
    assert result["added"] == []
    assert result["removed"] == []
    assert result["changed"] == []


def test_diff_added(project):
    set_secret(project, "OLD", "x")
    capture_baseline(project)
    set_secret(project, "NEW", "y")
    result = diff_from_baseline(project)
    assert "NEW" in result["added"]


def test_diff_removed(project):
    set_secret(project, "GONE", "x")
    capture_baseline(project)
    delete_secret(project, "GONE")
    result = diff_from_baseline(project)
    assert "GONE" in result["removed"]


def test_diff_changed(project):
    set_secret(project, "K", "old")
    capture_baseline(project)
    set_secret(project, "K", "new")
    result = diff_from_baseline(project)
    assert "K" in result["changed"]
