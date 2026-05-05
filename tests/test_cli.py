"""Integration tests for the main envault CLI (envault/cli.py)."""

import pytest
from unittest.mock import patch

from envault.cli import build_parser, main
from envault.storage import get_vault_dir


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_HOME", str(tmp_path))
    yield tmp_path


def run_cli(*argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


def test_init_project(capsys):
    run_cli("init", "myapp")
    captured = capsys.readouterr()
    assert "myapp" in captured.out
    assert "registered" in captured.out


def test_list_projects_empty(capsys):
    run_cli("projects")
    captured = capsys.readouterr()
    assert "No projects" in captured.out


def test_list_projects_shows_registered(capsys):
    run_cli("init", "alpha")
    run_cli("init", "beta")
    run_cli("projects")
    captured = capsys.readouterr()
    assert "alpha" in captured.out
    assert "beta" in captured.out


def test_remove_project(capsys):
    run_cli("init", "todelete")
    run_cli("remove", "todelete")
    captured = capsys.readouterr()
    assert "removed" in captured.out


def test_set_and_get_secret(capsys):
    run_cli("init", "proj")
    run_cli("set", "proj", "DB_URL", "postgres://localhost/db")
    run_cli("get", "proj", "DB_URL")
    captured = capsys.readouterr()
    assert "postgres://localhost/db" in captured.out


def test_list_secrets_empty(capsys):
    run_cli("init", "proj")
    run_cli("secrets", "proj")
    captured = capsys.readouterr()
    assert "No secrets" in captured.out


def test_list_secrets(capsys):
    run_cli("init", "proj")
    run_cli("set", "proj", "API_KEY", "abc123")
    run_cli("secrets", "proj")
    captured = capsys.readouterr()
    assert "API_KEY" in captured.out


def test_delete_secret(capsys):
    run_cli("init", "proj")
    run_cli("set", "proj", "TOKEN", "xyz")
    run_cli("delete", "proj", "TOKEN")
    captured = capsys.readouterr()
    assert "deleted" in captured.out


def test_audit_log(capsys):
    run_cli("init", "proj")
    run_cli("set", "proj", "KEY", "val")
    run_cli("audit", "proj")
    captured = capsys.readouterr()
    assert "set" in captured.out


def test_clear_audit(capsys):
    run_cli("init", "proj")
    run_cli("set", "proj", "KEY", "val")
    run_cli("clear-audit", "proj")
    run_cli("audit", "proj")
    captured = capsys.readouterr()
    assert "No audit events" in captured.out


def test_main_exits_on_error(monkeypatch):
    monkeypatch.setattr("sys.argv", ["envault", "get", "nonexistent", "KEY"])
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
