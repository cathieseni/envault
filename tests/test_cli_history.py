"""Tests for envault.cli_history CLI commands."""

import os
import subprocess
import sys
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.history import record_change


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_project(isolated_vault):
    register_project("testapp")
    set_secret("testapp", "TOKEN", "abc123")
    return "testapp"


def make_env(tmp_path):
    """Return a copy of the current environment with ENVAULT_VAULT_DIR set."""
    return {**os.environ, "ENVAULT_VAULT_DIR": str(tmp_path)}


def run(args, env):
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_history"] + args,
        capture_output=True, text=True, env=env
    )


def test_show_history_success(setup_project, monkeypatch, tmp_path):
    record_change("testapp", "TOKEN", "old", "new", actor="tester")
    result = run(["show", "testapp", "TOKEN"], make_env(tmp_path))
    assert result.returncode == 0
    assert "TOKEN" in result.stdout
    assert "tester" in result.stdout


def test_show_missing_key_exits_nonzero(setup_project, monkeypatch, tmp_path):
    result = run(["show", "testapp", "GHOST"], make_env(tmp_path))
    assert result.returncode != 0
    assert "Error" in result.stderr


def test_show_missing_project_exits_nonzero(isolated_vault, tmp_path):
    result = run(["show", "noproject", "KEY"], make_env(tmp_path))
    assert result.returncode != 0


def test_clear_history_success(setup_project, tmp_path):
    record_change("testapp", "TOKEN", "a", "b")
    result = run(["clear", "testapp", "TOKEN"], make_env(tmp_path))
    assert result.returncode == 0
    assert "Cleared" in result.stdout


def test_all_history_lists_keys(setup_project, tmp_path):
    record_change("testapp", "TOKEN", "x", "y")
    result = run(["all", "testapp"], make_env(tmp_path))
    assert result.returncode == 0
    assert "TOKEN" in result.stdout


def test_all_history_empty_project(setup_project, tmp_path):
    result = run(["all", "testapp"], make_env(tmp_path))
    assert result.returncode == 0
    assert "No history" in result.stdout
