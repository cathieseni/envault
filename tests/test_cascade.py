"""Tests for envault.cascade."""

import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret, list_secrets
from envault.cascade import cascade_secret, _find_dependents
from envault.dependencies import add_dependency


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def two_projects(isolated_vault):
    register_project("src")
    register_project("dst")
    set_secret("src", "DB_PASS", "s3cr3t")
    return isolated_vault


def test_cascade_propagates_to_explicit_target(two_projects):
    result = cascade_secret("src", "DB_PASS", targets=["dst"])
    assert "dst" in result.propagated_to
    assert get_secret("dst", "DB_PASS") == "s3cr3t"


def test_cascade_skips_when_no_overwrite(two_projects):
    set_secret("dst", "DB_PASS", "old_value")
    result = cascade_secret("src", "DB_PASS", targets=["dst"], overwrite=False)
    assert "dst" in result.skipped
    assert get_secret("dst", "DB_PASS") == "old_value"


def test_cascade_overwrites_by_default(two_projects):
    set_secret("dst", "DB_PASS", "old_value")
    result = cascade_secret("src", "DB_PASS", targets=["dst"], overwrite=True)
    assert "dst" in result.propagated_to
    assert get_secret("dst", "DB_PASS") == "s3cr3t"


def test_cascade_records_error_for_missing_target(two_projects):
    result = cascade_secret("src", "DB_PASS", targets=["nonexistent"])
    assert "nonexistent" in result.errors
    assert result.propagated_to == []


def test_cascade_missing_source_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        cascade_secret("ghost", "KEY", targets=["dst"])


def test_cascade_missing_key_raises(two_projects):
    with pytest.raises(KeyError):
        cascade_secret("src", "MISSING_KEY", targets=["dst"])


def test_find_dependents_via_dependency(two_projects):
    add_dependency("dst", "DB_PASS", "src")
    dependents = _find_dependents("src", "DB_PASS")
    assert "dst" in dependents


def test_find_dependents_empty_when_no_deps(two_projects):
    dependents = _find_dependents("src", "DB_PASS")
    assert dependents == []


def test_cascade_summary_contains_key_and_project(two_projects):
    result = cascade_secret("src", "DB_PASS", targets=["dst"])
    summary = result.summary()
    assert "DB_PASS" in summary
    assert "src" in summary
    assert "dst" in summary


def test_cascade_multiple_targets(isolated_vault):
    register_project("src")
    register_project("a")
    register_project("b")
    set_secret("src", "TOKEN", "abc123")
    result = cascade_secret("src", "TOKEN", targets=["a", "b"])
    assert set(result.propagated_to) == {"a", "b"}
    assert get_secret("a", "TOKEN") == "abc123"
    assert get_secret("b", "TOKEN") == "abc123"
