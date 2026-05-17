"""CLI integration tests for envault-group commands."""

from __future__ import annotations

import subprocess
import sys

import pytest

from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_HOST", "localhost")
    set_secret("myapp", "API_KEY", "abc123")
    return "myapp"


def run(*args, env_home):
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_grouping", *args],
        capture_output=True,
        text=True,
        env={"ENVAULT_HOME": str(env_home), "PATH": "/usr/bin:/bin"},
    )


def test_add_success(setup_project, isolated_vault):
    result = run("add", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    assert result.returncode == 0
    assert "Added" in result.stdout


def test_add_missing_key_exits_nonzero(setup_project, isolated_vault):
    result = run("add", "myapp", "database", "MISSING", env_home=isolated_vault)
    assert result.returncode != 0
    assert "Error" in result.stderr


def test_list_groups(setup_project, isolated_vault):
    run("add", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    result = run("list", "myapp", env_home=isolated_vault)
    assert result.returncode == 0
    assert "database" in result.stdout


def test_members_command(setup_project, isolated_vault):
    run("add", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    result = run("members", "myapp", "database", env_home=isolated_vault)
    assert result.returncode == 0
    assert "DB_HOST" in result.stdout


def test_remove_success(setup_project, isolated_vault):
    run("add", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    result = run("remove", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    assert result.returncode == 0
    assert "Removed" in result.stdout


def test_delete_group_success(setup_project, isolated_vault):
    run("add", "myapp", "database", "DB_HOST", env_home=isolated_vault)
    result = run("delete", "myapp", "database", env_home=isolated_vault)
    assert result.returncode == 0
    assert "Deleted" in result.stdout


def test_delete_missing_group_exits_nonzero(setup_project, isolated_vault):
    result = run("delete", "myapp", "ghost", env_home=isolated_vault)
    assert result.returncode != 0
