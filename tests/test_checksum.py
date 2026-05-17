"""Tests for envault.checksum."""

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.checksum import (
    record_checksum,
    verify_checksum,
    get_checksum,
    clear_checksum,
    audit_all,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_record_checksum_returns_hex(project):
    set_secret(project, "API_KEY", "supersecret")
    digest = record_checksum(project, "API_KEY")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


def test_get_checksum_after_record(project):
    set_secret(project, "TOKEN", "abc123")
    digest = record_checksum(project, "TOKEN")
    assert get_checksum(project, "TOKEN") == digest


def test_get_checksum_returns_none_when_not_recorded(project):
    set_secret(project, "TOKEN", "abc123")
    assert get_checksum(project, "TOKEN") is None


def test_verify_checksum_true_when_unchanged(project):
    set_secret(project, "DB_PASS", "hunter2")
    record_checksum(project, "DB_PASS")
    assert verify_checksum(project, "DB_PASS") is True


def test_verify_checksum_false_after_value_change(project):
    set_secret(project, "DB_PASS", "hunter2")
    record_checksum(project, "DB_PASS")
    set_secret(project, "DB_PASS", "newpassword")
    assert verify_checksum(project, "DB_PASS") is False


def test_verify_checksum_false_when_not_recorded(project):
    set_secret(project, "DB_PASS", "hunter2")
    assert verify_checksum(project, "DB_PASS") is False


def test_record_checksum_missing_key_raises(project):
    with pytest.raises(KeyError):
        record_checksum(project, "NONEXISTENT")


def test_verify_checksum_missing_key_raises(project):
    with pytest.raises(KeyError):
        verify_checksum(project, "GHOST")


def test_clear_checksum_removes_entry(project):
    set_secret(project, "X", "val")
    record_checksum(project, "X")
    clear_checksum(project, "X")
    assert get_checksum(project, "X") is None


def test_clear_checksum_noop_when_absent(project):
    # Should not raise
    clear_checksum(project, "MISSING")


def test_audit_all_statuses(project):
    set_secret(project, "A", "val_a")
    set_secret(project, "B", "val_b")
    set_secret(project, "C", "val_c")
    record_checksum(project, "A")
    record_checksum(project, "B")
    # Tamper with B
    set_secret(project, "B", "tampered")
    # C is untracked
    result = audit_all(project)
    assert result["A"] == "ok"
    assert result["B"] == "tampered"
    assert result["C"] == "untracked"
