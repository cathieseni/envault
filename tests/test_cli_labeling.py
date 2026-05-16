"""CLI integration tests for envault-label commands."""

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.labeling import set_label
from envault.cli_labeling import build_parser, cmd_label_set, cmd_label_list


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("myapp")
    set_secret("myapp", "DB_PASS", "hunter2")
    set_secret("myapp", "API_KEY", "abc")
    return "myapp"


def run(args, capsys=None):
    parser = build_parser()
    parsed = parser.parse_args(args)
    parsed.func(parsed)
    if capsys:
        return capsys.readouterr()
    return None


def test_set_success(setup_project, capsys):
    out, _ = run(["set", "myapp", "DB_PASS", "env", "production"], capsys)
    assert "env=production" in out


def test_set_missing_key_exits_nonzero(setup_project):
    parser = build_parser()
    args = parser.parse_args(["set", "myapp", "MISSING", "env", "prod"])
    with pytest.raises(SystemExit) as exc:
        args.func(args)
    assert exc.value.code != 0


def test_list_shows_labels(setup_project, capsys):
    set_label("myapp", "DB_PASS", "env", "staging")
    out, _ = run(["list", "myapp", "DB_PASS"], capsys)
    assert "env=staging" in out


def test_list_empty(setup_project, capsys):
    out, _ = run(["list", "myapp", "API_KEY"], capsys)
    assert "No labels" in out


def test_remove_success(setup_project, capsys):
    set_label("myapp", "DB_PASS", "env", "prod")
    out, _ = run(["remove", "myapp", "DB_PASS", "env"], capsys)
    assert "removed" in out


def test_remove_missing_label_exits_nonzero(setup_project):
    parser = build_parser()
    args = parser.parse_args(["remove", "myapp", "DB_PASS", "ghost"])
    with pytest.raises(SystemExit) as exc:
        args.func(args)
    assert exc.value.code != 0


def test_find_by_label(setup_project, capsys):
    set_label("myapp", "DB_PASS", "tier", "gold")
    set_label("myapp", "API_KEY", "tier", "silver")
    out, _ = run(["find", "myapp", "tier", "gold"], capsys)
    assert "DB_PASS" in out
    assert "API_KEY" not in out


def test_clear_success(setup_project, capsys):
    set_label("myapp", "DB_PASS", "env", "prod")
    out, _ = run(["clear", "myapp", "DB_PASS"], capsys)
    assert "cleared" in out
