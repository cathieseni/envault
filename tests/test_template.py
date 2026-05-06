"""Tests for envault.template and envault.cli_template."""

import os
import pytest
from pathlib import Path

from envault.storage import get_vault_dir
from envault.project import register_project
from envault.secrets import set_secret
from envault.template import render_template, list_placeholders


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path))
    yield tmp_path


@pytest.fixture()
def project(isolated_vault):
    register_project("myapp", str(isolated_vault / "myapp"))
    set_secret("myapp", "DB_HOST", "localhost")
    set_secret("myapp", "DB_PASS", "s3cr3t")
    return "myapp"


@pytest.fixture()
def template_file(tmp_path):
    tpl = tmp_path / "app.env.template"
    tpl.write_text("DB_HOST={{ DB_HOST }}\nDB_PASS={{ DB_PASS }}\n")
    return str(tpl)


def test_render_replaces_placeholders(project, template_file):
    result = render_template(project, template_file)
    assert "DB_HOST=localhost" in result
    assert "DB_PASS=s3cr3t" in result


def test_render_writes_output_file(project, template_file, tmp_path):
    out = str(tmp_path / "out" / ".env")
    render_template(project, template_file, output_path=out)
    content = Path(out).read_text()
    assert "DB_HOST=localhost" in content


def test_render_missing_template_raises(project, tmp_path):
    with pytest.raises(FileNotFoundError):
        render_template(project, str(tmp_path / "nonexistent.tpl"))


def test_render_missing_secret_raises(project, tmp_path):
    tpl = tmp_path / "bad.tpl"
    tpl.write_text("VAL={{ UNDEFINED_KEY }}\n")
    with pytest.raises(KeyError, match="UNDEFINED_KEY"):
        render_template(project, str(tpl))


def test_list_placeholders_returns_keys(template_file):
    keys = list_placeholders(template_file)
    assert keys == ["DB_HOST", "DB_PASS"]


def test_list_placeholders_deduplicates(tmp_path):
    tpl = tmp_path / "dup.tpl"
    tpl.write_text("{{ FOO }} and {{ FOO }} again\n")
    keys = list_placeholders(str(tpl))
    assert keys == ["FOO"]


def test_list_placeholders_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        list_placeholders(str(tmp_path / "ghost.tpl"))


def test_render_no_placeholders(project, tmp_path):
    tpl = tmp_path / "plain.env"
    tpl.write_text("STATIC=value\n")
    result = render_template(project, str(tpl))
    assert result == "STATIC=value\n"
