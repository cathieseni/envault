"""Tests for envault.labeling module."""

import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.labeling import (
    set_label,
    remove_label,
    get_labels,
    find_by_label,
    clear_labels,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_PASS", "s3cr3t")
    set_secret("myapp", "API_KEY", "abc123")
    return "myapp"


def test_set_label_stores_entry(project):
    set_label(project, "DB_PASS", "env", "production")
    labels = get_labels(project, "DB_PASS")
    assert labels["env"] == "production"


def test_set_label_multiple_labels(project):
    set_label(project, "DB_PASS", "env", "production")
    set_label(project, "DB_PASS", "owner", "devops")
    labels = get_labels(project, "DB_PASS")
    assert labels == {"env": "production", "owner": "devops"}


def test_set_label_overwrites_existing(project):
    set_label(project, "DB_PASS", "env", "staging")
    set_label(project, "DB_PASS", "env", "production")
    assert get_labels(project, "DB_PASS")["env"] == "production"


def test_set_label_missing_key_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        set_label(project, "MISSING", "env", "production")


def test_set_label_invalid_label_key_raises(project):
    with pytest.raises(ValueError, match="identifier"):
        set_label(project, "DB_PASS", "bad-key!", "val")


def test_remove_label(project):
    set_label(project, "DB_PASS", "env", "production")
    remove_label(project, "DB_PASS", "env")
    assert get_labels(project, "DB_PASS") == {}


def test_remove_label_missing_raises(project):
    with pytest.raises(KeyError):
        remove_label(project, "DB_PASS", "nonexistent")


def test_get_labels_empty_when_none_set(project):
    assert get_labels(project, "API_KEY") == {}


def test_find_by_label_key_only(project):
    set_label(project, "DB_PASS", "env", "production")
    set_label(project, "API_KEY", "env", "staging")
    results = find_by_label(project, "env")
    assert set(results.keys()) == {"DB_PASS", "API_KEY"}


def test_find_by_label_key_and_value(project):
    set_label(project, "DB_PASS", "env", "production")
    set_label(project, "API_KEY", "env", "staging")
    results = find_by_label(project, "env", "production")
    assert list(results.keys()) == ["DB_PASS"]


def test_find_by_label_no_match(project):
    results = find_by_label(project, "env", "production")
    assert results == {}


def test_clear_labels(project):
    set_label(project, "DB_PASS", "env", "production")
    set_label(project, "DB_PASS", "owner", "devops")
    clear_labels(project, "DB_PASS")
    assert get_labels(project, "DB_PASS") == {}


def test_clear_labels_noop_when_empty(project):
    # Should not raise
    clear_labels(project, "API_KEY")
    assert get_labels(project, "API_KEY") == {}
