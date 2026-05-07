"""Tests for envault.import_env module."""

import os
import pytest

import envault.storage as storage
from envault.project import register_project
from envault.secrets import get_secret
from envault.import_env import parse_dotenv, import_from_file


@pytest.fixture()
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_VAULT_DIR_OVERRIDE", str(tmp_path / "vault"))
    return tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp")
    return "myapp"


# --- parse_dotenv ---

def test_parse_simple_pairs():
    content = "FOO=bar\nBAZ=qux\n"
    result = parse_dotenv(content)
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_ignores_comments():
    content = "# comment\nKEY=value  # inline\n"
    result = parse_dotenv(content)
    assert result == {"KEY": "value"}


def test_parse_double_quoted_value():
    result = parse_dotenv('DB_URL="postgres://localhost/db"')
    assert result["DB_URL"] == "postgres://localhost/db"


def test_parse_single_quoted_value():
    result = parse_dotenv("SECRET='my secret value'")
    assert result["SECRET"] == "my secret value"


def test_parse_export_prefix():
    result = parse_dotenv("export API_KEY=abc123")
    assert result["API_KEY"] == "abc123"


def test_parse_empty_value():
    result = parse_dotenv("EMPTY=")
    assert result["EMPTY"] == ""


def test_parse_skips_invalid_lines():
    result = parse_dotenv("not-valid\nGOOD=yes")
    assert result == {"GOOD": "yes"}


def test_parse_blank_lines_ignored():
    """Blank lines and whitespace-only lines should be silently skipped."""
    content = "\n  \nFOO=bar\n\nBAZ=qux\n  \n"
    result = parse_dotenv(content)
    assert result == {"FOO": "bar", "BAZ": "qux"}


# --- import_from_file ---

def test_import_from_file_basic(project, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TOKEN=secret123\nDEBUG=true\n")
    imported, skipped = import_from_file(project, str(env_file))
    assert imported == 2
    assert skipped == 0
    assert get_secret(project, "TOKEN") == "secret123"
    assert get_secret(project, "DEBUG") == "true"


def test_import_skips_existing_without_overwrite(project, tmp_path):
    from envault.secrets import set_secret
    set_secret(project, "TOKEN", "original")
    env_file = tmp_path / ".env"
    env_file.write_text("TOKEN=newvalue\n")
    imported, skipped = import_from_file(project, str(env_file))
    assert imported == 0
    assert skipped == 1
    assert get_secret(project, "TOKEN") == "original"


def test_import_overwrites_when_flag_set(project, tmp_path):
    from envault.secrets import set_secret
    set_secret(project, "TOKEN", "original")
    env_file = tmp_path / ".env"
    env_file.write_text("TOKEN=newvalue\n")
    imported, skipped = import_from_file(project, str(env_file), overwrite=True)
    assert imported == 1
    assert skipped == 0
    assert get_secret(project, "TOKEN") == "newvalue"


def test_import_raises_for_missing_file(project):
    with pytest.raises(FileNotFoundError):
        import_from_file(project, "/nonexistent/.env")


def test_import_returns_correct_counts_mixed(project, tmp_path):
    """When some keys exist and some are new, counts should reflect each case."""
    from envault.secrets import set_secret
    set_secret(project, "EXISTING", "old")
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=updated\nNEW_KEY=fresh\n")
    imported, skipped = import_from_file(project, str(env_file))
    assert imported == 1
    assert skipped == 1
    assert get_secret(project, "EXISTING") == "old"
    assert get_secret(project, "NEW_KEY") == "fresh"
