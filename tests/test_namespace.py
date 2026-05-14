"""Tests for envault.namespace."""

import pytest

from envault.namespace import (
    set_in_namespace,
    get_in_namespace,
    list_namespace,
    delete_namespace,
    list_namespaces,
    _qualify,
)
from envault.secrets import set_secret, get_secret


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    from envault.project import register_project
    register_project("myapp")
    return "myapp"


def test_qualify_format():
    assert _qualify("db", "password") == "db:password"


def test_set_and_get_in_namespace(project):
    fqk = set_in_namespace(project, "db", "password", "s3cr3t")
    assert fqk == "db:password"
    assert get_in_namespace(project, "db", "password") == "s3cr3t"


def test_get_missing_key_raises(project):
    with pytest.raises(KeyError):
        get_in_namespace(project, "db", "nonexistent")


def test_list_namespace_returns_bare_keys(project):
    set_in_namespace(project, "cache", "host", "localhost")
    set_in_namespace(project, "cache", "port", "6379")
    set_in_namespace(project, "db", "host", "dbhost")
    result = list_namespace(project, "cache")
    assert result == {"host": "localhost", "port": "6379"}


def test_list_namespace_empty(project):
    result = list_namespace(project, "nonexistent")
    assert result == {}


def test_delete_namespace_removes_keys(project):
    set_in_namespace(project, "api", "key", "abc")
    set_in_namespace(project, "api", "secret", "xyz")
    set_in_namespace(project, "db", "url", "postgres://")
    removed = delete_namespace(project, "api")
    assert sorted(removed) == ["api:key", "api:secret"]
    assert list_namespace(project, "api") == {}
    assert list_namespace(project, "db") == {"url": "postgres://"}


def test_delete_namespace_no_keys(project):
    removed = delete_namespace(project, "ghost")
    assert removed == []


def test_list_namespaces(project):
    set_in_namespace(project, "db", "host", "h")
    set_in_namespace(project, "cache", "ttl", "60")
    set_in_namespace(project, "db", "port", "5432")
    # plain key without namespace should not appear
    set_secret(project, "plain_key", "value")
    ns = list_namespaces(project)
    assert ns == ["cache", "db"]


def test_list_namespaces_empty(project):
    set_secret(project, "no_namespace", "val")
    assert list_namespaces(project) == []


def test_set_in_namespace_missing_project(isolated_vault):
    with pytest.raises(KeyError):
        set_in_namespace("ghost_project", "ns", "k", "v")
