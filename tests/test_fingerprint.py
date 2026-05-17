"""Tests for envault.fingerprint."""

import pytest

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.fingerprint import (
    record_fingerprint,
    get_fingerprint,
    verify_fingerprint,
    delete_fingerprint,
    list_fingerprints,
    _hash_value,
)


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def project():
    register_project("myapp")
    set_secret("myapp", "DB_PASS", "s3cr3t")
    set_secret("myapp", "API_KEY", "abc123")
    return "myapp"


def test_hash_value_returns_16_char_hex():
    fp = _hash_value("hello")
    assert len(fp) == 16
    assert all(c in "0123456789abcdef" for c in fp)


def test_hash_value_is_deterministic():
    assert _hash_value("same") == _hash_value("same")


def test_hash_value_differs_for_different_inputs():
    assert _hash_value("a") != _hash_value("b")


def test_record_fingerprint_returns_hex(project):
    fp = record_fingerprint(project, "DB_PASS", "s3cr3t")
    assert isinstance(fp, str) and len(fp) == 16


def test_get_fingerprint_after_record(project):
    fp = record_fingerprint(project, "DB_PASS", "s3cr3t")
    assert get_fingerprint(project, "DB_PASS") == fp


def test_get_fingerprint_returns_none_when_not_recorded(project):
    assert get_fingerprint(project, "DB_PASS") is None


def test_verify_fingerprint_true_when_value_unchanged(project):
    record_fingerprint(project, "DB_PASS", "s3cr3t")
    assert verify_fingerprint(project, "DB_PASS", "s3cr3t") is True


def test_verify_fingerprint_false_when_value_changed(project):
    record_fingerprint(project, "DB_PASS", "s3cr3t")
    assert verify_fingerprint(project, "DB_PASS", "newvalue") is False


def test_verify_fingerprint_false_when_not_recorded(project):
    assert verify_fingerprint(project, "DB_PASS", "s3cr3t") is False


def test_delete_fingerprint_returns_true_when_existed(project):
    record_fingerprint(project, "DB_PASS", "s3cr3t")
    assert delete_fingerprint(project, "DB_PASS") is True
    assert get_fingerprint(project, "DB_PASS") is None


def test_delete_fingerprint_returns_false_when_missing(project):
    assert delete_fingerprint(project, "DB_PASS") is False


def test_list_fingerprints_returns_all(project):
    record_fingerprint(project, "DB_PASS", "s3cr3t")
    record_fingerprint(project, "API_KEY", "abc123")
    fps = list_fingerprints(project)
    assert set(fps.keys()) == {"DB_PASS", "API_KEY"}


def test_list_fingerprints_empty_initially(project):
    assert list_fingerprints(project) == {}


def test_record_fingerprint_unknown_project_raises():
    with pytest.raises(KeyError):
        record_fingerprint("ghost", "KEY", "val")
