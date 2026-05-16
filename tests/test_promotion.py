"""Tests for envault.promotion."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret, get_secret, list_secrets
from envault.promotion import promote_project, PromotionResult


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def two_projects(isolated_vault):
    register_project("staging")
    register_project("production")
    set_secret("staging", "DB_HOST", "db.staging.example.com")
    set_secret("staging", "DB_PASS", "s3cr3t")
    set_secret("staging", "API_KEY", "abc123")
    return isolated_vault


def test_promote_all_keys(two_projects):
    result = promote_project("staging", "production")
    assert set(result.promoted) == {"DB_HOST", "DB_PASS", "API_KEY"}
    assert result.skipped == []
    assert result.overwritten == []
    assert get_secret("production", "DB_HOST") == "db.staging.example.com"


def test_promote_subset_of_keys(two_projects):
    result = promote_project("staging", "production", keys=["DB_HOST"])
    assert result.promoted == ["DB_HOST"]
    assert "DB_PASS" not in list_secrets("production")


def test_promote_skips_existing_by_default(two_projects):
    set_secret("production", "DB_HOST", "prod-host")
    result = promote_project("staging", "production")
    assert "DB_HOST" in result.skipped
    # original production value must be preserved
    assert get_secret("production", "DB_HOST") == "prod-host"


def test_promote_overwrite_replaces_existing(two_projects):
    set_secret("production", "DB_HOST", "prod-host")
    result = promote_project("staging", "production", overwrite=True)
    assert "DB_HOST" in result.overwritten
    assert get_secret("production", "DB_HOST") == "db.staging.example.com"


def test_promote_with_prefix(two_projects):
    result = promote_project("staging", "production", keys=["API_KEY"], prefix="STG_")
    assert "STG_API_KEY" in result.promoted
    assert get_secret("production", "STG_API_KEY") == "abc123"


def test_promote_missing_key_raises(two_projects):
    with pytest.raises(KeyError, match="NONEXISTENT"):
        promote_project("staging", "production", keys=["NONEXISTENT"])


def test_promote_missing_source_raises(isolated_vault):
    register_project("production")
    with pytest.raises(KeyError):
        promote_project("ghost", "production")


def test_promote_missing_target_raises(isolated_vault):
    register_project("staging")
    with pytest.raises(KeyError):
        promote_project("staging", "ghost")


def test_summary_format(two_projects):
    result = promote_project("staging", "production")
    summary = result.summary()
    assert "staging" in summary
    assert "production" in summary
    assert "Promoted" in summary
