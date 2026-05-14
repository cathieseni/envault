"""CLI integration tests for envault-namespace."""

import subprocess
import sys
import pytest

from envault.namespace import set_in_namespace


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    from envault.project import register_project
    register_project("myapp")
    return "myapp"


def run(args, env_home):
    import os
    env = os.environ.copy()
    env["ENVAULT_HOME"] = str(env_home)
    return subprocess.run(
        [sys.executable, "-m", "envault.cli_namespace"] + args,
        capture_output=True,
        text=True,
        env=env,
    )


def test_set_and_get(setup_project, isolated_vault):
    r = run(["set", "myapp", "db", "password", "hunter2"], isolated_vault)
    assert r.returncode == 0
    assert "db:password" in r.stdout

    r2 = run(["get", "myapp", "db", "password"], isolated_vault)
    assert r2.returncode == 0
    assert "hunter2" in r2.stdout


def test_get_missing_key_exits_nonzero(setup_project, isolated_vault):
    r = run(["get", "myapp", "db", "missing"], isolated_vault)
    assert r.returncode == 1


def test_list_namespace(setup_project, isolated_vault):
    set_in_namespace("myapp", "cache", "host", "localhost")
    set_in_namespace("myapp", "cache", "port", "6379")
    r = run(["list", "myapp", "cache"], isolated_vault)
    assert r.returncode == 0
    assert "host" in r.stdout
    assert "port" in r.stdout


def test_list_namespace_empty(setup_project, isolated_vault):
    r = run(["list", "myapp", "empty_ns"], isolated_vault)
    assert r.returncode == 0
    assert "No secrets" in r.stdout


def test_delete_namespace(setup_project, isolated_vault):
    set_in_namespace("myapp", "api", "key", "abc")
    r = run(["delete", "myapp", "api"], isolated_vault)
    assert r.returncode == 0
    assert "api:key" in r.stdout


def test_namespaces_command(setup_project, isolated_vault):
    set_in_namespace("myapp", "db", "url", "postgres://")
    set_in_namespace("myapp", "redis", "host", "localhost")
    r = run(["namespaces", "myapp"], isolated_vault)
    assert r.returncode == 0
    assert "db" in r.stdout
    assert "redis" in r.stdout
