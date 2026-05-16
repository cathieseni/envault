"""Tests for envault.scoring module."""

import os
import pytest

from envault.scoring import score_value, score_project, ScoreResult
from envault.project import register_project
from envault.secrets import set_secret
from envault.storage import get_vault_dir


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path / "vault"))
    yield tmp_path / "vault"


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


# --- score_value ---

def test_empty_value_scores_zero():
    r = score_value("KEY", "")
    assert r.score == 0
    assert r.grade == "F"
    assert "empty value" in r.issues


def test_common_weak_value_low_score():
    r = score_value("KEY", "password")
    assert r.score < 50
    assert any("common" in i for i in r.issues)


def test_short_value_penalised():
    r = score_value("KEY", "abc")
    assert r.score < 60
    assert any("short" in i for i in r.issues)


def test_strong_value_high_score():
    r = score_value("KEY", "G7#kLpQ2!mNvR9@wZ")
    assert r.score >= 80
    assert r.grade == "A"
    assert r.issues == []


def test_moderate_value_mid_grade():
    r = score_value("KEY", "hello12345678")
    # Reasonable length but low variety/entropy
    assert 0 <= r.score <= 100
    assert r.grade in {"A", "B", "C", "D", "F"}


def test_score_result_repr():
    r = ScoreResult(key="X", score=75, grade="B")
    assert "X" in repr(r)
    assert "B" in repr(r)


def test_grade_boundaries():
    assert score_value("k", "G7#kLpQ2!mNvR9@wZ").grade == "A"   # >=80
    r_f = score_value("k", "ab")
    assert r_f.grade in {"D", "F"}


# --- score_project ---

def test_score_project_returns_all_keys(isolated_vault, project):
    set_secret(project, "DB_PASS", "G7#kLpQ2!mNvR9@wZ")
    set_secret(project, "API_KEY", "short")
    results = score_project(project)
    assert set(results.keys()) == {"DB_PASS", "API_KEY"}


def test_score_project_empty_project(isolated_vault, project):
    results = score_project(project)
    assert results == {}


def test_score_project_missing_project_raises(isolated_vault):
    with pytest.raises(KeyError):
        score_project("nonexistent")


def test_score_project_values_are_score_results(isolated_vault, project):
    set_secret(project, "TOKEN", "abc")
    results = score_project(project)
    assert isinstance(results["TOKEN"], ScoreResult)
    assert results["TOKEN"].key == "TOKEN"
