"""CLI tests for envault.cli_trust"""

from __future__ import annotations

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.cli_trust import build_parser


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "API_KEY", "s3cr3t")
    set_secret("myapp", "DB_PASS", "hunter2")
    return "myapp"


def run(args: list[str]):
    parser = build_parser()
    parsed = parser.parse_args(args)
    return parsed.func(parsed)


def test_set_success(setup_project):
    rc = run(["set", "myapp", "API_KEY", "trusted"])
    assert rc == 0


def test_set_invalid_level_exits_nonzero(setup_project, capsys):
    rc = run(["set", "myapp", "API_KEY", "trusted"])  # valid first
    # Now test invalid via direct call to avoid argparse sys.exit
    from envault.cli_trust import cmd_trust_set
    import argparse
    args = argparse.Namespace(project="myapp", key="API_KEY", level="bogus", note="")
    rc = cmd_trust_set(args)
    assert rc == 1


def test_set_missing_key_exits_nonzero(setup_project):
    from envault.cli_trust import cmd_trust_set
    import argparse
    args = argparse.Namespace(project="myapp", key="GHOST", level="trusted", note="")
    rc = cmd_trust_set(args)
    assert rc == 1


def test_get_after_set(setup_project, capsys):
    run(["set", "myapp", "API_KEY", "verified", "--note", "ok"])
    rc = run(["get", "myapp", "API_KEY"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "verified" in out


def test_get_missing_exits_nonzero(setup_project):
    rc = run(["get", "myapp", "API_KEY"])
    assert rc == 1


def test_list_shows_entries(setup_project, capsys):
    run(["set", "myapp", "API_KEY", "trusted"])
    run(["set", "myapp", "DB_PASS", "untrusted"])
    rc = run(["list", "myapp"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" in out


def test_filter_by_level(setup_project, capsys):
    run(["set", "myapp", "API_KEY", "trusted"])
    run(["set", "myapp", "DB_PASS", "untrusted"])
    rc = run(["filter", "myapp", "trusted"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" not in out


def test_remove_existing(setup_project, capsys):
    run(["set", "myapp", "API_KEY", "trusted"])
    rc = run(["remove", "myapp", "API_KEY"])
    assert rc == 0


def test_remove_nonexistent_exits_nonzero(setup_project):
    rc = run(["remove", "myapp", "API_KEY"])
    assert rc == 1
