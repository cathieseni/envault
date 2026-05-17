"""Tests for envault.cli_synopsis."""

from __future__ import annotations

import subprocess
import sys
import os
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.tag import add_tag


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("webapp")
    set_secret("webapp", "DB_PASS", "s3cr3t!")
    set_secret("webapp", "API_KEY", "abcdef123456")
    add_tag("webapp", "DB_PASS", "database")
    return "webapp"


def run(args, env):
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_synopsis"] + args,
        capture_output=True,
        text=True,
        env=env,
    )


def test_show_synopsis_exits_zero(setup_project, isolated_vault):
    env = {**os.environ, "ENVAULT_DIR": str(isolated_vault)}
    result = run(["show", "webapp"], env)
    assert result.returncode == 0


def test_show_synopsis_contains_project_name(setup_project, isolated_vault):
    env = {**os.environ, "ENVAULT_DIR": str(isolated_vault)}
    result = run(["show", "webapp"], env)
    assert "webapp" in result.stdout


def test_show_synopsis_verbose_shows_keys(setup_project, isolated_vault):
    env = {**os.environ, "ENVAULT_DIR": str(isolated_vault)}
    result = run(["show", "webapp", "--verbose"], env)
    assert "DB_PASS" in result.stdout
    assert "API_KEY" in result.stdout


def test_show_synopsis_missing_project_exits_nonzero(isolated_vault):
    env = {**os.environ, "ENVAULT_DIR": str(isolated_vault)}
    result = run(["show", "ghost"], env)
    assert result.returncode != 0
    assert "not found" in result.stderr


def test_show_synopsis_verbose_shows_tags(setup_project, isolated_vault):
    env = {**os.environ, "ENVAULT_DIR": str(isolated_vault)}
    result = run(["show", "webapp", "-v"], env)
    assert "database" in result.stdout
