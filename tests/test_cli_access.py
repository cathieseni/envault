"""Integration tests for the envault-access CLI."""

import pytest

from envault import storage, project as proj, secrets as sec
from envault.cli_access import build_parser


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "get_vault_dir", lambda: tmp_path / ".envault")
    (tmp_path / ".envault").mkdir()


@pytest.fixture()
def setup_project(isolated_vault):
    proj.register_project("myapp", "/tmp/myapp")
    sec.set_secret("myapp", "TOKEN", "tok123")
    sec.set_secret("myapp", "SECRET", "s3c")


def run(args: list[str], capsys) -> tuple[str, str]:
    parser = build_parser()
    parsed = parser.parse_args(args)
    parsed.func(parsed)
    captured = capsys.readouterr()
    return captured.out, captured.err


def test_grant_success(setup_project, capsys):
    out, _ = run(["grant", "myapp", "ci", "TOKEN"], capsys)
    assert "Granted" in out


def test_grant_missing_key_exits(setup_project, capsys):
    with pytest.raises(SystemExit):
        run(["grant", "myapp", "ci", "NOPE"], capsys)


def test_revoke_success(setup_project, capsys):
    run(["grant", "myapp", "ci", "TOKEN"], capsys)
    out, _ = run(["revoke", "myapp", "ci", "TOKEN"], capsys)
    assert "Revoked" in out


def test_revoke_missing_exits(setup_project, capsys):
    with pytest.raises(SystemExit):
        run(["revoke", "myapp", "ci", "TOKEN"], capsys)


def test_list_keys(setup_project, capsys):
    run(["grant", "myapp", "ci", "TOKEN"], capsys)
    out, _ = run(["keys", "myapp", "ci"], capsys)
    assert "TOKEN" in out


def test_list_keys_empty(setup_project, capsys):
    out, _ = run(["keys", "myapp", "nobody"], capsys)
    assert "No keys" in out


def test_list_profiles(setup_project, capsys):
    run(["grant", "myapp", "ci", "TOKEN"], capsys)
    run(["grant", "myapp", "dev", "SECRET"], capsys)
    out, _ = run(["profiles", "myapp"], capsys)
    assert "ci" in out
    assert "dev" in out


def test_list_profiles_empty(setup_project, capsys):
    out, _ = run(["profiles", "myapp"], capsys)
    assert "No profiles" in out
