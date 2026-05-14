"""Tests for envault.merge module."""

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret, list_secrets
from envault.lock import lock_secret
from envault.merge import merge_projects, MergeResult


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def two_projects(isolated_vault):
    register_project("src")
    register_project("dst")
    set_secret("src", "KEY_A", "alpha")
    set_secret("src", "KEY_B", "bravo")
    set_secret("src", "KEY_C", "charlie")
    return isolated_vault


def test_merge_adds_new_keys(two_projects):
    result = merge_projects("src", "dst")
    assert set(result.added) == {"KEY_A", "KEY_B", "KEY_C"}
    assert result.skipped == []
    assert result.overwritten == []
    assert result.errors == []
    assert get_secret("dst", "KEY_A") == "alpha"


def test_merge_skip_conflict(two_projects):
    set_secret("dst", "KEY_A", "original")
    result = merge_projects("src", "dst", conflict="skip")
    assert "KEY_A" in result.skipped
    assert "KEY_B" in result.added
    # original value preserved
    assert get_secret("dst", "KEY_A") == "original"


def test_merge_overwrite_conflict(two_projects):
    set_secret("dst", "KEY_A", "original")
    result = merge_projects("src", "dst", conflict="overwrite")
    assert "KEY_A" in result.overwritten
    assert get_secret("dst", "KEY_A") == "alpha"


def test_merge_error_conflict_raises(two_projects):
    set_secret("dst", "KEY_B", "existing")
    with pytest.raises(ValueError, match="KEY_B"):
        merge_projects("src", "dst", conflict="error")


def test_merge_with_key_filter(two_projects):
    result = merge_projects("src", "dst", keys=["KEY_A", "KEY_C"])
    assert set(result.added) == {"KEY_A", "KEY_C"}
    assert "KEY_B" not in list_secrets("dst")


def test_merge_locked_key_skipped_with_error_in_result(two_projects):
    set_secret("dst", "KEY_A", "locked_value")
    lock_secret("dst", "KEY_A")
    result = merge_projects("src", "dst", conflict="overwrite")
    assert "KEY_A" in result.errors
    # locked value must not change
    assert get_secret("dst", "KEY_A") == "locked_value"


def test_merge_locked_key_raises_on_error_strategy(two_projects):
    set_secret("dst", "KEY_A", "locked_value")
    lock_secret("dst", "KEY_A")
    with pytest.raises(ValueError, match="locked"):
        merge_projects("src", "dst", conflict="error")


def test_merge_missing_src_raises(isolated_vault):
    register_project("dst")
    with pytest.raises(KeyError):
        merge_projects("nonexistent", "dst")


def test_merge_missing_dst_raises(isolated_vault):
    register_project("src")
    set_secret("src", "X", "1")
    with pytest.raises(KeyError):
        merge_projects("src", "nonexistent")


def test_merge_returns_named_tuple(two_projects):
    result = merge_projects("src", "dst")
    assert isinstance(result, MergeResult)
    assert hasattr(result, "added")
    assert hasattr(result, "skipped")
    assert hasattr(result, "overwritten")
    assert hasattr(result, "errors")
