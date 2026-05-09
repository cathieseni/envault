"""Tests for envault.clone."""

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret, list_secrets
from envault.tag import add_tag, list_tags
from envault.clone import clone_project


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def two_projects(isolated_vault):
    register_project("src")
    register_project("dst")
    return "src", "dst"


def test_clone_copies_all_secrets(two_projects):
    src, dst = two_projects
    set_secret(src, "DB_URL", "postgres://localhost")
    set_secret(src, "API_KEY", "abc123")

    report = clone_project(src, dst)

    assert report == {"DB_URL": "cloned", "API_KEY": "cloned"}
    assert get_secret(dst, "DB_URL") == "postgres://localhost"
    assert get_secret(dst, "API_KEY") == "abc123"


def test_clone_skips_existing_by_default(two_projects):
    src, dst = two_projects
    set_secret(src, "KEY", "new_value")
    set_secret(dst, "KEY", "old_value")

    report = clone_project(src, dst)

    assert report["KEY"] == "skipped"
    assert get_secret(dst, "KEY") == "old_value"


def test_clone_overwrite_replaces_existing(two_projects):
    src, dst = two_projects
    set_secret(src, "KEY", "new_value")
    set_secret(dst, "KEY", "old_value")

    report = clone_project(src, dst, overwrite=True)

    assert report["KEY"] == "cloned"
    assert get_secret(dst, "KEY") == "new_value"


def test_clone_filters_by_tag(two_projects):
    src, dst = two_projects
    set_secret(src, "DB_URL", "postgres://localhost")
    set_secret(src, "API_KEY", "abc123")
    add_tag(src, "DB_URL", "database")

    report = clone_project(src, dst, tag="database")

    assert "DB_URL" in report
    assert report["DB_URL"] == "cloned"
    assert "API_KEY" not in report
    assert list_secrets(dst) == ["DB_URL"]


def test_clone_mirrors_tags(two_projects):
    src, dst = two_projects
    set_secret(src, "DB_URL", "postgres://localhost")
    add_tag(src, "DB_URL", "database")
    add_tag(src, "DB_URL", "prod")

    clone_project(src, dst)

    dst_tags = list_tags(dst, "DB_URL")
    assert "database" in dst_tags
    assert "prod" in dst_tags


def test_clone_missing_src_raises(isolated_vault):
    register_project("dst")
    with pytest.raises(KeyError):
        clone_project("nonexistent", "dst")


def test_clone_missing_dst_raises(isolated_vault):
    register_project("src")
    with pytest.raises(KeyError):
        clone_project("src", "nonexistent")


def test_clone_empty_src_returns_empty_report(two_projects):
    src, dst = two_projects
    report = clone_project(src, dst)
    assert report == {}
