import pytest
import os
import tempfile
from unittest import mock
from envault.project import register_project
from envault.secrets import set_secret, get_secret, delete_secret, list_secrets, rotate_secret
from envault.audit import log_event, get_audit_log, clear_audit_log


@pytest.fixture
def isolated_vault(tmp_path):
    with mock.patch("envault.storage.get_vault_dir", return_value=str(tmp_path)):
        yield tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp", str(isolated_vault / "myapp"))
    return "myapp"


def test_set_and_get_secret(project):
    set_secret(project, "DB_PASSWORD", "supersecret")
    assert get_secret(project, "DB_PASSWORD") == "supersecret"


def test_get_missing_secret_raises(project):
    with pytest.raises(KeyError, match="DB_HOST"):
        get_secret(project, "DB_HOST")


def test_delete_secret(project):
    set_secret(project, "API_KEY", "abc123")
    delete_secret(project, "API_KEY")
    with pytest.raises(KeyError):
        get_secret(project, "API_KEY")


def test_delete_missing_secret_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        delete_secret(project, "MISSING")


def test_list_secrets(project):
    set_secret(project, "FOO", "bar")
    set_secret(project, "BAZ", "qux")
    result = list_secrets(project)
    keys = [s["key"] for s in result]
    assert "FOO" in keys
    assert "BAZ" in keys
    for entry in result:
        assert "updated_at" in entry


def test_rotate_secret(project):
    set_secret(project, "TOKEN", "old_value")
    rotate_secret(project, "TOKEN", "new_value")
    assert get_secret(project, "TOKEN") == "new_value"


def test_rotate_missing_secret_raises(project):
    with pytest.raises(KeyError):
        rotate_secret(project, "NONEXISTENT", "value")


def test_audit_log_event_and_retrieve(project):
    log_event(project, "set", "DB_URL", actor="test")
    log_event(project, "get", "DB_URL", actor="test")
    entries = get_audit_log(project)
    assert len(entries) == 2
    assert entries[0]["action"] == "set"
    assert entries[1]["action"] == "get"
    assert entries[0]["key"] == "DB_URL"


def test_audit_log_empty_for_new_project(project):
    assert get_audit_log(project) == []


def test_clear_audit_log(project):
    log_event(project, "set", "X", actor="cli")
    clear_audit_log(project)
    assert get_audit_log(project) == []
