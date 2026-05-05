"""Tests for envault.export module."""

import json
import os
import pytest

from envault.export import export_secrets, _to_dotenv, _to_json, _to_shell
from envault.project import register_project
from envault.secrets import set_secret
from envault.storage import get_vault_dir


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def project():
    register_project("myapp")
    set_secret("myapp", "DB_HOST", "localhost")
    set_secret("myapp", "API_KEY", 'abc"def')
    return "myapp"


# --- format helpers ---

def test_to_dotenv_escapes_quotes():
    result = _to_dotenv({"KEY": 'val"ue'})
    assert result == 'KEY="val\\"ue"'


def test_to_json_valid():
    result = _to_json({"A": "1", "B": "2"})
    data = json.loads(result)
    assert data == {"A": "1", "B": "2"}


def test_to_shell_escapes_single_quotes():
    result = _to_shell({"KEY": "it's"})
    assert result == "export KEY='it'\"'\"'s'"


# --- export_secrets integration ---

def test_export_dotenv(project):
    output = export_secrets(project, fmt="dotenv")
    assert 'DB_HOST="localhost"' in output
    assert 'API_KEY=' in output


def test_export_json(project):
    output = export_secrets(project, fmt="json")
    data = json.loads(output)
    assert data["DB_HOST"] == "localhost"


def test_export_shell(project):
    output = export_secrets(project, fmt="shell")
    assert "export DB_HOST='localhost'" in output


def test_export_redact(project):
    output = export_secrets(project, fmt="dotenv", redact=True)
    assert '"***"' in output
    assert "localhost" not in output


def test_export_unknown_format_raises(project):
    with pytest.raises(ValueError, match="Unknown export format"):
        export_secrets(project, fmt="xml")  # type: ignore[arg-type]


def test_export_missing_project_raises():
    with pytest.raises(KeyError):
        export_secrets("ghost", fmt="dotenv")


def test_export_logs_audit_event(project):
    from envault.audit import get_audit_log
    export_secrets(project, fmt="json")
    log = get_audit_log(project)
    assert any(entry["action"] == "export" for entry in log)
