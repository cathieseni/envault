"""Tests for envault.alias."""

from __future__ import annotations

import pytest

from envault.alias import add_alias, get_via_alias, list_aliases, remove_alias, resolve_alias
from envault.project import register_project
from envault.secrets import set_secret
from envault.storage import get_vault_dir


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path / "vault"))
    return tmp_path / "vault"


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DATABASE_URL", "postgres://localhost/db")
    set_secret("myapp", "API_KEY", "supersecret")
    return "myapp"


def test_add_alias_stores_mapping(project):
    add_alias(project, "DB", "DATABASE_URL")
    aliases = list_aliases(project)
    assert aliases["DB"] == "DATABASE_URL"


def test_add_alias_missing_key_raises(project):
    with pytest.raises(KeyError):
        add_alias(project, "GHOST", "NONEXISTENT_KEY")


def test_add_alias_duplicate_raises(project):
    add_alias(project, "DB", "DATABASE_URL")
    with pytest.raises(ValueError, match="already exists"):
        add_alias(project, "DB", "API_KEY")


def test_remove_alias(project):
    add_alias(project, "DB", "DATABASE_URL")
    remove_alias(project, "DB")
    assert "DB" not in list_aliases(project)


def test_remove_alias_missing_raises(project):
    with pytest.raises(KeyError):
        remove_alias(project, "DOES_NOT_EXIST")


def test_resolve_alias_returns_target(project):
    add_alias(project, "DB", "DATABASE_URL")
    assert resolve_alias(project, "DB") == "DATABASE_URL"


def test_resolve_alias_passthrough_for_non_alias(project):
    # A key that is not an alias should resolve to itself
    assert resolve_alias(project, "DATABASE_URL") == "DATABASE_URL"


def test_get_via_alias_returns_value(project):
    add_alias(project, "DB", "DATABASE_URL")
    value = get_via_alias(project, "DB")
    assert value == "postgres://localhost/db"


def test_get_via_alias_direct_key(project):
    # Works even without an alias registered
    value = get_via_alias(project, "API_KEY")
    assert value == "supersecret"


def test_list_aliases_empty_initially(project):
    assert list_aliases(project) == {}


def test_list_aliases_multiple(project):
    add_alias(project, "DB", "DATABASE_URL")
    add_alias(project, "KEY", "API_KEY")
    aliases = list_aliases(project)
    assert len(aliases) == 2
    assert aliases["KEY"] == "API_KEY"
