"""Tests for envault.cli_lint CLI command."""

from __future__ import annotations

import pytest

from envault.project import register_project
from envault.secrets import set_secret
from envault.cli_lint import build_parser, cmd_lint


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def setup_project(isolated_vault):
    register_project("webapp")
    return "webapp"


def run(args: list[str]):
    parser = build_parser()
    return parser.parse_args(args)


def test_lint_no_issues_exits_zero(setup_project, capsys):
    set_secret("webapp", "API_SECRET", "strongrandomvalue99")
    args = run(["webapp"])
    cmd_lint(args)  # should not raise or call sys.exit
    captured = capsys.readouterr()
    assert "No issues found" in captured.out


def test_lint_error_exits_nonzero(setup_project):
    set_secret("webapp", "DB_PASSWORD", "secret")
    args = run(["webapp"])
    with pytest.raises(SystemExit) as exc_info:
        cmd_lint(args)
    assert exc_info.value.code == 1


def test_lint_warning_does_not_exit(setup_project, capsys):
    set_secret("webapp", "SHORT", "abc12")
    args = run(["webapp"])
    # short value (< 8 chars) is a warning, not an error — should not sys.exit
    cmd_lint(args)
    captured = capsys.readouterr()
    assert "WARNING" in captured.out


def test_lint_output_contains_key_name(setup_project, capsys):
    set_secret("webapp", "WEAK_TOKEN", "admin")
    args = run(["webapp"])
    with pytest.raises(SystemExit):
        cmd_lint(args)
    captured = capsys.readouterr()
    assert "WEAK_TOKEN" in captured.out
