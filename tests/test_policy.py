"""Tests for envault.policy."""

from __future__ import annotations

import pytest

from envault.policy import (
    PolicyViolation,
    audit_project,
    get_policy,
    reset_policy,
    set_policy,
    validate_value,
)
from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


# ---------------------------------------------------------------------------
# get_policy / set_policy / reset_policy
# ---------------------------------------------------------------------------

def test_get_policy_returns_defaults(project):
    policy = get_policy(project)
    assert policy["min_length"] == 8
    assert policy["require_uppercase"] is False


def test_set_policy_updates_fields(project):
    updated = set_policy(project, min_length=16, require_digit=True)
    assert updated["min_length"] == 16
    assert updated["require_digit"] is True


def test_set_policy_ignores_unknown_keys(project):
    updated = set_policy(project, nonexistent_key="value")
    assert "nonexistent_key" not in updated


def test_set_policy_persists(project):
    set_policy(project, min_length=20)
    assert get_policy(project)["min_length"] == 20


def test_reset_policy_restores_defaults(project):
    set_policy(project, min_length=32)
    reset_policy(project)
    assert get_policy(project)["min_length"] == 8


# ---------------------------------------------------------------------------
# validate_value
# ---------------------------------------------------------------------------

def test_validate_passes_for_valid_value(project):
    validate_value(project, "API_KEY", "abcdefgh")  # no exception


def test_validate_raises_when_too_short(project):
    set_policy(project, min_length=12)
    with pytest.raises(PolicyViolation, match="too short"):
        validate_value(project, "TOKEN", "short")


def test_validate_raises_when_too_long(project):
    set_policy(project, max_length=5)
    with pytest.raises(PolicyViolation, match="too long"):
        validate_value(project, "TOKEN", "toolongvalue")


def test_validate_requires_uppercase(project):
    set_policy(project, require_uppercase=True)
    with pytest.raises(PolicyViolation, match="uppercase"):
        validate_value(project, "KEY", "alllowercase")


def test_validate_requires_digit(project):
    set_policy(project, require_digit=True)
    with pytest.raises(PolicyViolation, match="digit"):
        validate_value(project, "KEY", "NoDigitsHere")


def test_validate_requires_special(project):
    set_policy(project, require_special=True)
    with pytest.raises(PolicyViolation, match="special"):
        validate_value(project, "KEY", "NoSpecialChar1")


def test_validate_disallows_key(project):
    set_policy(project, disallow_keys=["FORBIDDEN"])
    with pytest.raises(PolicyViolation, match="disallowed"):
        validate_value(project, "FORBIDDEN", "anyvalue123")


# ---------------------------------------------------------------------------
# audit_project
# ---------------------------------------------------------------------------

def test_audit_clean_project(project):
    set_secret(project, "DB_PASS", "securepassword1")
    violations = audit_project(project)
    assert violations == []


def test_audit_detects_violations(project):
    set_secret(project, "WEAK", "tiny")
    set_policy(project, min_length=8)
    violations = audit_project(project)
    assert any("WEAK" in v for v in violations)


def test_audit_multiple_violations(project):
    set_policy(project, min_length=20)
    set_secret(project, "KEY1", "short")
    set_secret(project, "KEY2", "alsoshort")
    violations = audit_project(project)
    assert len(violations) == 2
