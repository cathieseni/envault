"""Tests for envault.synopsis."""

from __future__ import annotations

import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.tag import add_tag
from envault.lock import lock_secret
from envault.pin import pin_secret
from envault.synopsis import generate_synopsis, ProjectSynopsis


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


def test_generate_synopsis_returns_type(project):
    set_secret(project, "KEY1", "value1")
    syn = generate_synopsis(project)
    assert isinstance(syn, ProjectSynopsis)


def test_synopsis_total_secrets(project):
    set_secret(project, "A", "alpha")
    set_secret(project, "B", "beta")
    syn = generate_synopsis(project)
    assert syn.total_secrets == 2


def test_synopsis_empty_project(project):
    syn = generate_synopsis(project)
    assert syn.total_secrets == 0
    assert syn.avg_score == 0.0


def test_synopsis_locked_count(project):
    set_secret(project, "SEC", "password")
    lock_secret(project, "SEC")
    syn = generate_synopsis(project)
    assert syn.locked_count == 1


def test_synopsis_pinned_count(project):
    set_secret(project, "SEC", "password")
    pin_secret(project, "SEC")
    syn = generate_synopsis(project)
    assert syn.pinned_count == 1


def test_synopsis_tags_on_secret(project):
    set_secret(project, "SEC", "password")
    add_tag(project, "SEC", "critical")
    syn = generate_synopsis(project)
    sec = next(s for s in syn.secrets if s.key == "SEC")
    assert "critical" in sec.tags


def test_synopsis_avg_score_positive(project):
    set_secret(project, "GOOD", "Tr0ub4dor&3_secure_long_value!")
    syn = generate_synopsis(project)
    assert syn.avg_score > 0


def test_synopsis_missing_project_raises():
    with pytest.raises(KeyError):
        generate_synopsis("nonexistent_project")


def test_synopsis_summary_string(project):
    set_secret(project, "K", "v")
    syn = generate_synopsis(project)
    text = syn.summary()
    assert "myapp" in text
    assert "Secrets" in text
