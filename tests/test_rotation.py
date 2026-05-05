"""Tests for envault.rotation module."""

import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret
from envault.rotation import rotate_secret, rotate_all_secrets, _generate_secret_value
from envault.audit import get_audit_log
from envault.storage import get_vault_dir

import os
import tempfile


@pytest.fixture
def isolated_vault(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("rotation-test")
    return "rotation-test"


def test_generate_secret_value_length():
    val = _generate_secret_value(length=24)
    assert len(val) == 24


def test_generate_secret_value_custom_alphabet():
    val = _generate_secret_value(length=50, alphabet="abc")
    assert all(c in "abc" for c in val)


def test_rotate_secret_returns_old_and_new(project):
    set_secret(project, "API_KEY", "old-value-123")
    result = rotate_secret(project, "API_KEY")

    assert result["key"] == "API_KEY"
    assert result["old_value"] == "old-value-123"
    assert result["new_value"] != "old-value-123"
    assert len(result["new_value"]) == 32
    assert "rotated_at" in result


def test_rotate_secret_updates_stored_value(project):
    set_secret(project, "DB_PASS", "initial")
    result = rotate_secret(project, "DB_PASS")
    assert get_secret(project, "DB_PASS") == result["new_value"]


def test_rotate_secret_logs_audit_event(project):
    set_secret(project, "TOKEN", "abc")
    rotate_secret(project, "TOKEN")
    log = get_audit_log(project)
    rotate_events = [e for e in log if e["action"] == "rotate"]
    assert len(rotate_events) >= 1
    assert rotate_events[-1]["details"]["key"] == "TOKEN"


def test_rotate_missing_secret_raises(project):
    with pytest.raises(KeyError):
        rotate_secret(project, "NONEXISTENT")


def test_rotate_all_secrets(project):
    set_secret(project, "KEY_A", "val-a")
    set_secret(project, "KEY_B", "val-b")
    set_secret(project, "KEY_C", "val-c")

    results = rotate_all_secrets(project)
    assert len(results) == 3
    keys_rotated = {r["key"] for r in results}
    assert keys_rotated == {"KEY_A", "KEY_B", "KEY_C"}


def test_rotate_all_secrets_empty_project(project):
    results = rotate_all_secrets(project)
    assert results == []
