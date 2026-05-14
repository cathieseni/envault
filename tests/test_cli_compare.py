"""Tests for envault.cli_compare CLI entry point."""

import subprocess
import sys
import pytest

from envault.project import register_project
from envault.secrets import set_secret


@pytest.fixture
def isolated_vault(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_projects(isolated_vault):
    register_project("src")
    register_project("dst")
    set_secret("src", "COMMON", "val")
    set_secret("src", "ONLY_SRC", "s")
    set_secret("dst", "COMMON", "val")
    set_secret("dst", "ONLY_DST", "d")
    return isolated_vault


def run(vault_dir, *args):
    env = {"ENVAULT_VAULT_DIR": str(vault_dir)}
    import os
    full_env = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_compare", *args],
        capture_output=True,
        text=True,
        env=full_env,
    )


def test_compare_exits_nonzero_when_differences(setup_projects):
    result = run(setup_projects, "src", "dst")
    assert result.returncode == 1


def test_compare_shows_only_in_source(setup_projects):
    result = run(setup_projects, "src", "dst")
    assert "ONLY_SRC" in result.stdout


def test_compare_shows_only_in_target(setup_projects):
    result = run(setup_projects, "src", "dst")
    assert "ONLY_DST" in result.stdout


def test_compare_exits_zero_when_identical(isolated_vault):
    register_project("a")
    register_project("b")
    set_secret("a", "X", "1")
    set_secret("b", "X", "2")
    result = run(isolated_vault, "a", "b")
    assert result.returncode == 0
    assert "identical" in result.stdout


def test_compare_missing_project_exits_nonzero(isolated_vault):
    register_project("exists")
    result = run(isolated_vault, "exists", "missing")
    assert result.returncode == 1
    assert "Error" in result.stderr
