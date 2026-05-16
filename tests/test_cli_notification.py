"""CLI integration tests for envault-notify."""

import subprocess
import sys
import pytest

from envault.project import register_project


@pytest.fixture
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_VAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def setup_project(isolated_vault):
    register_project("testapp")
    return "testapp"


def run(*args, env_extra=None, isolated_vault=None):
    import os
    env = os.environ.copy()
    if isolated_vault:
        env["ENVAULT_VAULT_DIR"] = str(isolated_vault)
    result = subprocess.run(
        [sys.executable, "-m", "envault.cli_notification"] + list(args),
        capture_output=True, text=True, env=env
    )
    return result


def test_add_success(setup_project, isolated_vault):
    r = run("add", "testapp", "slack", "https://hooks.slack.com/abc", isolated_vault=isolated_vault)
    assert r.returncode == 0
    assert "Notification added" in r.stdout


def test_add_invalid_channel_exits_nonzero(setup_project, isolated_vault):
    r = run("add", "testapp", "fax", "555-0000", isolated_vault=isolated_vault)
    assert r.returncode != 0


def test_list_empty(setup_project, isolated_vault):
    r = run("list", "testapp", isolated_vault=isolated_vault)
    assert r.returncode == 0
    assert "No notifications" in r.stdout


def test_list_shows_entry(setup_project, isolated_vault):
    run("add", "testapp", "email", "admin@example.com", isolated_vault=isolated_vault)
    r = run("list", "testapp", isolated_vault=isolated_vault)
    assert "admin@example.com" in r.stdout


def test_remove_success(setup_project, isolated_vault):
    run("add", "testapp", "slack", "https://hooks.slack.com/abc", isolated_vault=isolated_vault)
    r = run("remove", "testapp", "https://hooks.slack.com/abc", isolated_vault=isolated_vault)
    assert r.returncode == 0
    assert "removed" in r.stdout


def test_remove_missing_exits_nonzero(setup_project, isolated_vault):
    r = run("remove", "testapp", "ghost", isolated_vault=isolated_vault)
    assert r.returncode != 0


def test_update_events(setup_project, isolated_vault):
    run("add", "testapp", "webhook", "https://my.api/hook", isolated_vault=isolated_vault)
    r = run("update", "testapp", "https://my.api/hook", "expire,delete", isolated_vault=isolated_vault)
    assert r.returncode == 0
    assert "expire" in r.stdout
