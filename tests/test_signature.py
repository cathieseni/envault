"""Tests for envault.signature."""

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.signature import (
    sign_secret,
    verify_secret,
    get_signature,
    remove_signature,
    list_signatures,
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


def test_sign_secret_returns_hex_string(project):
    sig = sign_secret(project, "DB_PASS")
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA-256 hex digest


def test_sign_secret_is_deterministic(project):
    sig1 = sign_secret(project, "DB_PASS")
    sig2 = sign_secret(project, "DB_PASS")
    assert sig1 == sig2


def test_sign_missing_key_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        sign_secret(project, "MISSING")


def test_verify_returns_true_when_unchanged(project):
    sign_secret(project, "DB_PASS")
    assert verify_secret(project, "DB_PASS") is True


def test_verify_returns_false_when_not_signed(project):
    assert verify_secret(project, "API_KEY") is False


def test_verify_returns_false_after_value_changes(project):
    sign_secret(project, "DB_PASS")
    set_secret(project, "DB_PASS", "new_value")
    assert verify_secret(project, "DB_PASS") is False


def test_verify_missing_key_raises(project):
    with pytest.raises(KeyError):
        verify_secret(project, "GHOST")


def test_get_signature_returns_none_when_not_signed(project):
    assert get_signature(project, "API_KEY") is None


def test_get_signature_returns_stored_value(project):
    sig = sign_secret(project, "API_KEY")
    assert get_signature(project, "API_KEY") == sig


def test_remove_signature_clears_entry(project):
    sign_secret(project, "DB_PASS")
    remove_signature(project, "DB_PASS")
    assert get_signature(project, "DB_PASS") is None


def test_remove_signature_missing_raises(project):
    with pytest.raises(KeyError):
        remove_signature(project, "DB_PASS")


def test_list_signatures_returns_all(project):
    sign_secret(project, "DB_PASS")
    sign_secret(project, "API_KEY")
    sigs = list_signatures(project)
    assert set(sigs.keys()) == {"DB_PASS", "API_KEY"}


def test_list_signatures_empty_when_none_signed(project):
    assert list_signatures(project) == {}
