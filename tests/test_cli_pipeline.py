"""Tests for envault.cli_pipeline."""
from __future__ import annotations

import json
import subprocess
import sys

import pytest

from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "TOKEN", "abc123")
    return "myapp"


def run(args: list[str], env=None) -> subprocess.CompletedProcess:
    import os
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_pipeline"] + args,
        capture_output=True, text=True, env=e,
    )


def test_create_and_list(setup_project, isolated_vault):
    steps = json.dumps([{"action": "get", "key": "TOKEN"}])
    r = run(["create", "myapp", "mypipe", steps], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode == 0
    assert "mypipe" in r.stdout

    r2 = run(["list", "myapp"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r2.returncode == 0
    assert "mypipe" in r2.stdout


def test_show_pipeline(setup_project, isolated_vault):
    steps = json.dumps([{"action": "get", "key": "TOKEN"}])
    run(["create", "myapp", "mypipe", steps], env={"ENVAULT_DIR": str(isolated_vault)})
    r = run(["show", "myapp", "mypipe"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data[0]["action"] == "get"


def test_delete_pipeline(setup_project, isolated_vault):
    steps = json.dumps([{"action": "get", "key": "TOKEN"}])
    run(["create", "myapp", "mypipe", steps], env={"ENVAULT_DIR": str(isolated_vault)})
    r = run(["delete", "myapp", "mypipe"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode == 0
    r2 = run(["list", "myapp"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert "mypipe" not in r2.stdout


def test_run_pipeline_exits_zero_on_success(setup_project, isolated_vault):
    steps = json.dumps([{"action": "get", "key": "TOKEN"}])
    run(["create", "myapp", "mypipe", steps], env={"ENVAULT_DIR": str(isolated_vault)})
    r = run(["run", "myapp", "mypipe"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode == 0
    results = json.loads(r.stdout)
    assert results[0]["status"] == "ok"


def test_run_pipeline_exits_nonzero_on_error(setup_project, isolated_vault):
    steps = json.dumps([{"action": "get", "key": "NO_SUCH_KEY"}])
    run(["create", "myapp", "badpipe", steps], env={"ENVAULT_DIR": str(isolated_vault)})
    r = run(["run", "myapp", "badpipe"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode != 0


def test_create_invalid_json_exits_nonzero(setup_project, isolated_vault):
    r = run(["create", "myapp", "pipe", "not-json"], env={"ENVAULT_DIR": str(isolated_vault)})
    assert r.returncode != 0
    assert "invalid JSON" in r.stderr
