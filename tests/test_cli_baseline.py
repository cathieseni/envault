"""Tests for envault.cli_baseline."""

from __future__ import annotations

import subprocess
import sys
import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.baseline import capture_baseline


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("app")
    set_secret("app", "DB_PASS", "secret123")
    return "app"


def run(isolated_vault, *args):
    env = {"ENVAULT_DIR": str(isolated_vault), "PATH": "/usr/bin:/bin"}
    import os
    env.update({k: v for k, v in os.environ.items() if k not in env})
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_baseline"] + list(args),
        capture_output=True, text=True, env=env,
    )


def test_capture_exits_zero(isolated_vault, setup_project):
    result = run(isolated_vault, "capture", "app")
    assert result.returncode == 0
    assert "app" in result.stdout


def test_show_after_capture(isolated_vault, setup_project):
    run(isolated_vault, "capture", "app")
    result = run(isolated_vault, "show", "app")
    assert result.returncode == 0
    assert "DB_PASS" in result.stdout


def test_show_no_baseline_exits_nonzero(isolated_vault, setup_project):
    result = run(isolated_vault, "show", "app")
    assert result.returncode != 0


def test_diff_no_drift_exits_zero(isolated_vault, setup_project):
    run(isolated_vault, "capture", "app")
    result = run(isolated_vault, "diff", "app")
    assert result.returncode == 0


def test_diff_with_drift_exits_nonzero(isolated_vault, setup_project):
    run(isolated_vault, "capture", "app")
    set_secret("app", "NEW_KEY", "newval")
    result = run(isolated_vault, "diff", "app")
    assert result.returncode != 0
    assert "+" in result.stdout


def test_clear_exits_zero(isolated_vault, setup_project):
    run(isolated_vault, "capture", "app")
    result = run(isolated_vault, "clear", "app")
    assert result.returncode == 0
    assert "cleared" in result.stdout
