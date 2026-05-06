"""Tests for envault.access module."""

import pytest

from envault import storage, project as proj, secrets as sec, access


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "get_vault_dir", lambda: tmp_path / ".envault")
    (tmp_path / ".envault").mkdir()


@pytest.fixture()
def project(isolated_vault):
    proj.register_project("acme", "/tmp/acme")
    sec.set_secret("acme", "DB_PASS", "s3cr3t")
    sec.set_secret("acme", "API_KEY", "abc123")
    return "acme"


def test_grant_stores_key(project):
    access.grant(project, "readonly", "DB_PASS")
    assert "DB_PASS" in access.list_profile_keys(project, "readonly")


def test_grant_idempotent(project):
    access.grant(project, "readonly", "DB_PASS")
    access.grant(project, "readonly", "DB_PASS")
    assert access.list_profile_keys(project, "readonly").count("DB_PASS") == 1


def test_grant_missing_key_raises(project):
    with pytest.raises(KeyError, match="MISSING"):
        access.grant(project, "readonly", "MISSING")


def test_revoke_removes_key(project):
    access.grant(project, "readonly", "DB_PASS")
    access.revoke(project, "readonly", "DB_PASS")
    assert "DB_PASS" not in access.list_profile_keys(project, "readonly")


def test_revoke_removes_empty_profile(project):
    access.grant(project, "readonly", "DB_PASS")
    access.revoke(project, "readonly", "DB_PASS")
    assert "readonly" not in access.list_profiles(project)


def test_revoke_missing_raises(project):
    with pytest.raises(KeyError):
        access.revoke(project, "readonly", "DB_PASS")


def test_can_access_true(project):
    access.grant(project, "ci", "API_KEY")
    assert access.can_access(project, "ci", "API_KEY") is True


def test_can_access_false(project):
    assert access.can_access(project, "ci", "API_KEY") is False


def test_list_profiles(project):
    access.grant(project, "ci", "API_KEY")
    access.grant(project, "dev", "DB_PASS")
    profiles = access.list_profiles(project)
    assert set(profiles) == {"ci", "dev"}
