"""Tests for envault.quota."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.quota import (
    QuotaExceededError,
    check_quota,
    clear_quota,
    enforce_quota,
    get_quota,
    set_quota,
)


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_default_quota_is_100(project):
    assert get_quota(project) == 100


def test_set_and_get_quota(project):
    set_quota(project, 10)
    assert get_quota(project) == 10


def test_set_quota_zero_raises(project):
    with pytest.raises(ValueError, match="at least 1"):
        set_quota(project, 0)


def test_set_quota_negative_raises(project):
    with pytest.raises(ValueError):
        set_quota(project, -5)


def test_clear_quota_reverts_to_default(project):
    set_quota(project, 5)
    clear_quota(project)
    assert get_quota(project) == 100


def test_clear_quota_idempotent(project):
    clear_quota(project)  # no quota file exists yet — should not raise
    assert get_quota(project) == 100


def test_check_quota_empty_project(project):
    current, limit, ok = check_quota(project)
    assert current == 0
    assert limit == 100
    assert ok is True


def test_check_quota_counts_secrets(project):
    set_secret(project, "KEY1", "val1")
    set_secret(project, "KEY2", "val2")
    current, limit, ok = check_quota(project)
    assert current == 2
    assert ok is True


def test_check_quota_exceeded(project):
    set_quota(project, 2)
    set_secret(project, "A", "1")
    set_secret(project, "B", "2")
    current, limit, ok = check_quota(project)
    assert current == 2
    assert limit == 2
    assert ok is False


def test_enforce_quota_passes_when_under_limit(project):
    set_quota(project, 5)
    set_secret(project, "X", "y")
    enforce_quota(project)  # should not raise


def test_enforce_quota_raises_when_at_limit(project):
    set_quota(project, 1)
    set_secret(project, "ONLY", "one")
    with pytest.raises(QuotaExceededError, match="myapp"):
        enforce_quota(project)
