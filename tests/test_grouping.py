"""Tests for envault.grouping."""

from __future__ import annotations

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.grouping import (
    add_to_group,
    remove_from_group,
    list_groups,
    get_group_members,
    delete_group,
    groups_for_key,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_HOST", "localhost")
    set_secret("myapp", "DB_PASS", "secret")
    set_secret("myapp", "API_KEY", "abc123")
    return "myapp"


def test_add_to_group_stores_key(project):
    add_to_group(project, "database", "DB_HOST")
    assert "DB_HOST" in get_group_members(project, "database")


def test_add_to_group_idempotent(project):
    add_to_group(project, "database", "DB_HOST")
    add_to_group(project, "database", "DB_HOST")
    assert get_group_members(project, "database").count("DB_HOST") == 1


def test_add_to_group_missing_key_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        add_to_group(project, "database", "MISSING")


def test_list_groups_returns_all(project):
    add_to_group(project, "database", "DB_HOST")
    add_to_group(project, "api", "API_KEY")
    groups = list_groups(project)
    assert set(groups) == {"database", "api"}


def test_list_groups_empty_initially(project):
    assert list_groups(project) == []


def test_get_group_members_unknown_group_returns_empty(project):
    assert get_group_members(project, "nonexistent") == []


def test_remove_from_group(project):
    add_to_group(project, "database", "DB_HOST")
    add_to_group(project, "database", "DB_PASS")
    remove_from_group(project, "database", "DB_HOST")
    assert "DB_HOST" not in get_group_members(project, "database")
    assert "DB_PASS" in get_group_members(project, "database")


def test_remove_last_key_deletes_group(project):
    add_to_group(project, "solo", "API_KEY")
    remove_from_group(project, "solo", "API_KEY")
    assert "solo" not in list_groups(project)


def test_remove_missing_key_raises(project):
    add_to_group(project, "database", "DB_HOST")
    with pytest.raises(KeyError):
        remove_from_group(project, "database", "API_KEY")


def test_delete_group(project):
    add_to_group(project, "database", "DB_HOST")
    delete_group(project, "database")
    assert "database" not in list_groups(project)


def test_delete_missing_group_raises(project):
    with pytest.raises(KeyError, match="ghost"):
        delete_group(project, "ghost")


def test_groups_for_key(project):
    add_to_group(project, "database", "DB_HOST")
    add_to_group(project, "infra", "DB_HOST")
    result = groups_for_key(project, "DB_HOST")
    assert set(result) == {"database", "infra"}


def test_groups_for_key_not_in_any_group(project):
    assert groups_for_key(project, "API_KEY") == []
