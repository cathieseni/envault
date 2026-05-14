"""Tests for envault.compare module."""

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.compare import compare_projects, compare_many, CompareResult
from envault.storage import get_vault_dir

import os
import tempfile


@pytest.fixture
def isolated_vault(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def two_projects(isolated_vault):
    register_project("alpha")
    register_project("beta")
    set_secret("alpha", "DB_URL", "postgres://localhost/alpha")
    set_secret("alpha", "API_KEY", "abc123")
    set_secret("alpha", "SHARED", "same")
    set_secret("beta", "REDIS_URL", "redis://localhost")
    set_secret("beta", "SHARED", "same")
    return "alpha", "beta"


def test_compare_only_in_source(two_projects):
    result = compare_projects("alpha", "beta")
    assert "DB_URL" in result.only_in_source
    assert "API_KEY" in result.only_in_source


def test_compare_only_in_target(two_projects):
    result = compare_projects("alpha", "beta")
    assert "REDIS_URL" in result.only_in_target


def test_compare_in_both(two_projects):
    result = compare_projects("alpha", "beta")
    assert "SHARED" in result.in_both


def test_compare_has_differences(two_projects):
    result = compare_projects("alpha", "beta")
    assert result.has_differences() is True


def test_compare_no_differences(isolated_vault):
    register_project("p1")
    register_project("p2")
    set_secret("p1", "KEY", "val")
    set_secret("p2", "KEY", "val")
    result = compare_projects("p1", "p2")
    assert result.has_differences() is False
    assert result.in_both == ["KEY"]


def test_compare_summary_keys(two_projects):
    result = compare_projects("alpha", "beta")
    summary = result.summary()
    assert set(summary.keys()) == {"only_in_source", "only_in_target", "in_both"}


def test_compare_missing_project_raises(isolated_vault):
    register_project("real")
    with pytest.raises(KeyError):
        compare_projects("real", "ghost")


def test_compare_many_returns_list(two_projects, isolated_vault):
    register_project("gamma")
    set_secret("gamma", "SHARED", "x")
    results = compare_many("alpha", ["beta", "gamma"])
    assert len(results) == 2
    assert all(isinstance(r, CompareResult) for r in results)
