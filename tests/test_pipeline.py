"""Tests for envault.pipeline."""
from __future__ import annotations

import os
import pytest

from envault.pipeline import (
    create_pipeline,
    get_pipeline,
    list_pipelines,
    delete_pipeline,
    run_pipeline,
)
from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


SIMPLE_STEPS = [
    {"action": "set", "key": "FOO", "value": "bar"},
    {"action": "get", "key": "FOO"},
]


def test_create_pipeline_stores_steps(project):
    create_pipeline(project, "setup", SIMPLE_STEPS)
    assert "setup" in list_pipelines(project)


def test_get_pipeline_returns_steps(project):
    create_pipeline(project, "setup", SIMPLE_STEPS)
    steps = get_pipeline(project, "setup")
    assert steps == SIMPLE_STEPS


def test_list_pipelines_empty(project):
    assert list_pipelines(project) == []


def test_create_pipeline_missing_action_raises(project):
    with pytest.raises(ValueError, match="action"):
        create_pipeline(project, "bad", [{"key": "X"}])


def test_get_pipeline_missing_raises(project):
    with pytest.raises(KeyError):
        get_pipeline(project, "nonexistent")


def test_delete_pipeline_removes_entry(project):
    create_pipeline(project, "setup", SIMPLE_STEPS)
    delete_pipeline(project, "setup")
    assert "setup" not in list_pipelines(project)


def test_delete_pipeline_missing_raises(project):
    with pytest.raises(KeyError):
        delete_pipeline(project, "ghost")


def test_run_pipeline_set_and_get(project):
    steps = [
        {"action": "set", "key": "DB_URL", "value": "postgres://localhost/db"},
        {"action": "get", "key": "DB_URL"},
    ]
    create_pipeline(project, "db_setup", steps)
    results = run_pipeline(project, "db_setup")
    assert results[0]["status"] == "ok"
    assert results[1]["status"] == "ok"
    assert results[1]["value"] == "postgres://localhost/db"


def test_run_pipeline_rotate(project):
    set_secret(project, "API_KEY", "old_value")
    steps = [{"action": "rotate", "key": "API_KEY"}]
    create_pipeline(project, "rotate_key", steps)
    results = run_pipeline(project, "rotate_key")
    assert results[0]["status"] == "ok"
    assert results[0]["old"] == "old_value"
    assert results[0]["new"] != "old_value"


def test_run_pipeline_unknown_action_records_error(project):
    steps = [{"action": "fly", "key": "X"}]
    create_pipeline(project, "bad_pipeline", steps)
    results = run_pipeline(project, "bad_pipeline")
    assert results[0]["status"] == "error"
    assert "Unknown action" in results[0]["error"]


def test_run_pipeline_missing_key_records_error(project):
    steps = [{"action": "get", "key": "MISSING_KEY"}]
    create_pipeline(project, "fail_pipe", steps)
    results = run_pipeline(project, "fail_pipe")
    assert results[0]["status"] == "error"
