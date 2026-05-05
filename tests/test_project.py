"""Tests for project registration and management."""

import os
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_vault(tmp_path, monkeypatch):
    """Redirect vault storage to a temporary directory for each test."""
    monkeypatch.setenv("ENVAULT_DIR", str(tmp_path / ".envault"))


def test_register_project(tmp_path):
    from envault.project import register_project, get_project

    project = register_project("myapp", str(tmp_path))
    assert project["name"] == "myapp"
    assert project["path"] == str(tmp_path.resolve())
    assert "created_at" in project

    fetched = get_project("myapp")
    assert fetched["name"] == "myapp"


def test_register_duplicate_raises(tmp_path):
    from envault.project import register_project

    register_project("myapp", str(tmp_path))
    with pytest.raises(ValueError, match="already exists"):
        register_project("myapp", str(tmp_path))


def test_list_projects(tmp_path):
    from envault.project import register_project, list_projects

    register_project("alpha", str(tmp_path))
    register_project("beta", str(tmp_path))

    projects = list_projects()
    names = [p["name"] for p in projects]
    assert "alpha" in names
    assert "beta" in names


def test_get_missing_project_raises():
    from envault.project import get_project

    with pytest.raises(KeyError, match="not found"):
        get_project("ghost")


def test_remove_project(tmp_path):
    from envault.project import register_project, remove_project, list_projects

    register_project("todelete", str(tmp_path))
    remove_project("todelete")

    names = [p["name"] for p in list_projects()]
    assert "todelete" not in names


def test_remove_missing_project_raises():
    from envault.project import remove_project

    with pytest.raises(KeyError, match="not found"):
        remove_project("nobody")
