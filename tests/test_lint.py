"""Tests for envault.lint module."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.lint import lint_project, _check_weak_value, _check_duplicate_values, _check_empty_values


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_lint_clean_project(project):
    set_secret(project, "API_KEY", "supersecretvalue123")
    issues = lint_project(project)
    assert issues == []


def test_lint_detects_weak_value(project):
    set_secret(project, "DB_PASS", "password")
    issues = lint_project(project)
    keys = [i["key"] for i in issues]
    assert "DB_PASS" in keys
    assert any(i["level"] == "error" for i in issues if i["key"] == "DB_PASS")


def test_lint_detects_short_value(project):
    set_secret(project, "TOKEN", "abc")
    issues = lint_project(project)
    assert any(i["key"] == "TOKEN" and i["level"] == "warning" for i in issues)


def test_lint_detects_empty_value(project):
    set_secret(project, "EMPTY_KEY", "   ")
    issues = lint_project(project)
    assert any(i["key"] == "EMPTY_KEY" and i["level"] == "error" for i in issues)


def test_lint_detects_duplicate_values(project):
    set_secret(project, "KEY_A", "sharedvalue99")
    set_secret(project, "KEY_B", "sharedvalue99")
    issues = lint_project(project)
    assert any("KEY_A" in i["key"] and "KEY_B" in i["key"] for i in issues)


def test_lint_missing_project_raises(isolated_vault):
    from envault.project import ProjectNotFoundError
    with pytest.raises(ProjectNotFoundError):
        lint_project("nonexistent")


def test_check_weak_value_known_word():
    issues = _check_weak_value("PASS", "changeme")
    assert any(i["level"] == "error" for i in issues)


def test_check_duplicate_values_no_dups():
    issues = _check_duplicate_values({"A": "val1", "B": "val2"})
    assert issues == []


def test_check_empty_values_non_empty():
    issues = _check_empty_values({"KEY": "somevalue"})
    assert issues == []
