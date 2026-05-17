"""Tests for envault.redaction."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.redaction import (
    set_redaction_rule,
    remove_redaction_rule,
    get_redaction_rule,
    list_redaction_rules,
    redact,
)


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "supersecret123")
    set_secret("myapp", "DB_PASS", "p@ssw0rd")
    return "myapp"


def test_set_and_get_rule(project):
    set_redaction_rule(project, "API_KEY")
    rule = get_redaction_rule(project, "API_KEY")
    assert rule is not None
    assert rule["mask"] == "***"
    assert rule["pattern"] is None


def test_set_rule_custom_mask(project):
    set_redaction_rule(project, "API_KEY", mask="[REDACTED]")
    rule = get_redaction_rule(project, "API_KEY")
    assert rule["mask"] == "[REDACTED]"


def test_set_rule_with_pattern(project):
    set_redaction_rule(project, "DB_PASS", pattern=r"\d+")
    rule = get_redaction_rule(project, "DB_PASS")
    assert rule["pattern"] == r"\d+"


def test_set_rule_missing_key_raises(project):
    with pytest.raises(KeyError):
        set_redaction_rule(project, "NONEXISTENT")


def test_get_rule_returns_none_when_not_set(project):
    assert get_redaction_rule(project, "API_KEY") is None


def test_remove_rule(project):
    set_redaction_rule(project, "API_KEY")
    remove_redaction_rule(project, "API_KEY")
    assert get_redaction_rule(project, "API_KEY") is None


def test_remove_rule_missing_raises(project):
    with pytest.raises(KeyError):
        remove_redaction_rule(project, "API_KEY")


def test_list_rules_empty(project):
    assert list_redaction_rules(project) == {}


def test_list_rules_returns_all(project):
    set_redaction_rule(project, "API_KEY")
    set_redaction_rule(project, "DB_PASS", mask="HIDDEN")
    rules = list_redaction_rules(project)
    assert set(rules.keys()) == {"API_KEY", "DB_PASS"}


def test_redact_full_value(project):
    set_redaction_rule(project, "API_KEY", mask="***")
    assert redact(project, "API_KEY", "supersecret123") == "***"


def test_redact_with_pattern(project):
    set_redaction_rule(project, "DB_PASS", mask="X", pattern=r"\d")
    result = redact(project, "DB_PASS", "p@ssw0rd")
    assert result == "p@ssw0rd".replace("0", "X")


def test_redact_no_rule_returns_original(project):
    assert redact(project, "API_KEY", "supersecret123") == "supersecret123"
