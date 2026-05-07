"""Tests for envault.search module."""

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.tag import add_tag
from envault.search import search_by_key, search_by_value, search_by_tag


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def two_projects():
    register_project("alpha")
    register_project("beta")
    set_secret("alpha", "DB_PASSWORD", "secret123")
    set_secret("alpha", "DB_HOST", "localhost")
    set_secret("alpha", "API_KEY", "abc")
    set_secret("beta", "DB_PASSWORD", "hunter2")
    set_secret("beta", "REDIS_URL", "redis://localhost")
    return ["alpha", "beta"]


# --- search_by_key ---

def test_search_by_key_glob_all_projects(two_projects):
    results = search_by_key("DB_*")
    keys = [(r["project"], r["key"]) for r in results]
    assert ("alpha", "DB_PASSWORD") in keys
    assert ("alpha", "DB_HOST") in keys
    assert ("beta", "DB_PASSWORD") in keys


def test_search_by_key_limited_to_project(two_projects):
    results = search_by_key("DB_*", project_name="alpha")
    projects = {r["project"] for r in results}
    assert projects == {"alpha"}


def test_search_by_key_no_match(two_projects):
    results = search_by_key("NONEXISTENT_*")
    assert results == []


def test_search_by_key_exact(two_projects):
    results = search_by_key("API_KEY")
    assert len(results) == 1
    assert results[0]["key"] == "API_KEY"
    assert results[0]["value"] == "abc"


# --- search_by_value ---

def test_search_by_value_glob(two_projects):
    results = search_by_value("*localhost*")
    keys = [r["key"] for r in results]
    assert "DB_HOST" in keys
    assert "REDIS_URL" in keys


def test_search_by_value_limited_to_project(two_projects):
    results = search_by_value("*localhost*", project_name="beta")
    assert all(r["project"] == "beta" for r in results)
    assert any(r["key"] == "REDIS_URL" for r in results)


def test_search_by_value_no_match(two_projects):
    results = search_by_value("ZZZNOTFOUND")
    assert results == []


# --- search_by_tag ---

def test_search_by_tag_finds_tagged_secrets(two_projects):
    add_tag("alpha", "DB_PASSWORD", "sensitive")
    add_tag("beta", "DB_PASSWORD", "sensitive")
    results = search_by_tag("sensitive")
    assert len(results) == 2
    for r in results:
        assert "sensitive" in r["tags"]


def test_search_by_tag_limited_to_project(two_projects):
    add_tag("alpha", "API_KEY", "external")
    add_tag("beta", "REDIS_URL", "external")
    results = search_by_tag("external", project_name="alpha")
    assert all(r["project"] == "alpha" for r in results)


def test_search_by_tag_no_match(two_projects):
    results = search_by_tag("nonexistent-tag")
    assert results == []
