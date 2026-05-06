"""Tests for envault tag management."""

import pytest
from pathlib import Path

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.tag import add_tag, remove_tag, list_tags, get_secrets_by_tag, all_tags


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "abc123")
    set_secret("myapp", "DB_PASS", "secret")
    set_secret("myapp", "TOKEN", "tok")
    return "myapp"


def test_add_tag_stores_tag(project):
    add_tag(project, "API_KEY", "production")
    assert "production" in list_tags(project, "API_KEY")


def test_add_tag_idempotent(project):
    add_tag(project, "API_KEY", "production")
    add_tag(project, "API_KEY", "production")
    assert list_tags(project, "API_KEY").count("production") == 1


def test_add_tag_missing_key_raises(project):
    with pytest.raises(KeyError):
        add_tag(project, "NONEXISTENT", "mytag")


def test_remove_tag(project):
    add_tag(project, "DB_PASS", "internal")
    remove_tag(project, "DB_PASS", "internal")
    assert "internal" not in list_tags(project, "DB_PASS")


def test_remove_tag_not_present_raises(project):
    with pytest.raises(ValueError):
        remove_tag(project, "DB_PASS", "ghost")


def test_list_tags_empty_by_default(project):
    assert list_tags(project, "TOKEN") == []


def test_get_secrets_by_tag_returns_matching_keys(project):
    add_tag(project, "API_KEY", "prod")
    add_tag(project, "TOKEN", "prod")
    result = get_secrets_by_tag(project, "prod")
    assert set(result.keys()) == {"API_KEY", "TOKEN"}


def test_get_secrets_by_tag_empty_when_no_match(project):
    result = get_secrets_by_tag(project, "nonexistent-tag")
    assert result == {}


def test_all_tags_returns_full_mapping(project):
    add_tag(project, "API_KEY", "public")
    mapping = all_tags(project)
    assert "API_KEY" in mapping
    assert "DB_PASS" in mapping
    assert "public" in mapping["API_KEY"]
    assert mapping["DB_PASS"] == []
