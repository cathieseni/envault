"""Tests for the envault-check CLI."""

import time
import subprocess
import sys
import pytest
from envault.project import register_project
from envault.secrets import set_secret
from envault.expiry import set_expiry


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_project(isolated_vault):
    register_project("testapp", "/tmp/testapp")
    set_secret("testapp", "DB_URL", "postgres://localhost")
    set_secret("testapp", "API_KEY", "secret123")
    return "testapp"


def run(args, env):
    result = subprocess.run(
        [sys.executable, "-m", "envault.cli_env_check"] + args,
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def test_check_all_ok_exits_zero(setup_project, isolated_vault, monkeypatch):
    import os
    env = os.environ.copy()
    env["ENVAULT_VAULT_DIR"] = str(isolated_vault)
    result = run(["testapp"], env)
    assert result.returncode == 0
    assert "✓" in result.stdout


def test_check_missing_key_exits_nonzero(setup_project, isolated_vault):
    import os
    env = os.environ.copy()
    env["ENVAULT_VAULT_DIR"] = str(isolated_vault)
    result = run(["testapp", "--keys", "MISSING_KEY"], env)
    assert result.returncode == 1
    assert "✗" in result.stdout


def test_check_expired_exits_nonzero(setup_project, isolated_vault):
    import os
    set_expiry("testapp", "API_KEY", time.time() - 1)
    env = os.environ.copy()
    env["ENVAULT_VAULT_DIR"] = str(isolated_vault)
    result = run(["testapp", "--keys", "API_KEY"], env)
    assert result.returncode == 1
    assert "!" in result.stdout


def test_check_unknown_project_exits_nonzero(isolated_vault):
    import os
    env = os.environ.copy()
    env["ENVAULT_VAULT_DIR"] = str(isolated_vault)
    result = run(["ghost_project"], env)
    assert result.returncode == 1
    assert "Error" in result.stderr
