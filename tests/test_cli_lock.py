"""Integration tests for cli_lock commands."""

from __future__ import annotations

import subprocess
import sys

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.lock import lock_secret


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "TOKEN", "supersecret")
    return "myapp"


def run(args, env_dir):
    import os
    env = os.environ.copy()
    env["ENVAULT_DIR"] = str(env_dir)
    result = subprocess.run(
        [sys.executable, "-m", "envault.cli_lock"] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def test_lock_success(setup_project, isolated_vault):
    result = run(["lock", "myapp", "TOKEN"], isolated_vault)
    assert result.returncode == 0
    assert "Locked" in result.stdout


def test_lock_missing_project_exits_nonzero(isolated_vault):
    result = run(["lock", "ghost", "KEY"], isolated_vault)
    assert result.returncode != 0


def test_unlock_success(setup_project, isolated_vault):
    lock_secret("myapp", "TOKEN")
    result = run(["unlock", "myapp", "TOKEN"], isolated_vault)
    assert result.returncode == 0
    assert "Unlocked" in result.stdout


def test_unlock_not_locked_exits_nonzero(setup_project, isolated_vault):
    result = run(["unlock", "myapp", "TOKEN"], isolated_vault)
    assert result.returncode != 0
    assert "not locked" in result.stderr.lower() or "error" in result.stderr.lower()


def test_list_locked_empty(setup_project, isolated_vault):
    result = run(["list", "myapp"], isolated_vault)
    assert result.returncode == 0
    assert "No locked" in result.stdout


def test_list_locked_shows_keys(setup_project, isolated_vault):
    lock_secret("myapp", "TOKEN")
    result = run(["list", "myapp"], isolated_vault)
    assert result.returncode == 0
    assert "TOKEN" in result.stdout
