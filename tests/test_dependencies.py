"""Tests for envault.dependencies."""
import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.dependencies import (
    add_dependency,
    remove_dependency,
    get_dependents,
    get_dependencies,
    clear_dependencies,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_PASSWORD", "secret1")
    set_secret("myapp", "DB_URL", "postgres://localhost")
    set_secret("myapp", "REPLICA_URL", "postgres://replica")
    return "myapp"


def test_add_dependency_stores_entry(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    assert "DB_URL" in get_dependents(project, "DB_PASSWORD")


def test_add_dependency_idempotent(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    assert get_dependents(project, "DB_PASSWORD").count("DB_URL") == 1


def test_add_dependency_missing_key_raises(project):
    with pytest.raises(KeyError):
        add_dependency(project, "MISSING", "DB_PASSWORD")


def test_add_dependency_missing_parent_raises(project):
    with pytest.raises(KeyError):
        add_dependency(project, "DB_URL", "MISSING")


def test_add_dependency_self_raises(project):
    with pytest.raises(ValueError):
        add_dependency(project, "DB_URL", "DB_URL")


def test_get_dependents_multiple(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    add_dependency(project, "REPLICA_URL", "DB_PASSWORD")
    deps = get_dependents(project, "DB_PASSWORD")
    assert set(deps) == {"DB_URL", "REPLICA_URL"}


def test_get_dependencies_returns_parents(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    parents = get_dependencies(project, "DB_URL")
    assert "DB_PASSWORD" in parents


def test_get_dependents_empty_when_none(project):
    assert get_dependents(project, "DB_PASSWORD") == []


def test_remove_dependency(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    remove_dependency(project, "DB_URL", "DB_PASSWORD")
    assert get_dependents(project, "DB_PASSWORD") == []


def test_remove_nonexistent_dependency_raises(project):
    with pytest.raises(KeyError):
        remove_dependency(project, "DB_URL", "DB_PASSWORD")


def test_clear_dependencies_removes_as_parent(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    clear_dependencies(project, "DB_PASSWORD")
    assert get_dependents(project, "DB_PASSWORD") == []


def test_clear_dependencies_removes_as_child(project):
    add_dependency(project, "DB_URL", "DB_PASSWORD")
    clear_dependencies(project, "DB_URL")
    assert "DB_URL" not in get_dependents(project, "DB_PASSWORD")
