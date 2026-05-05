"""Persistent storage layer for envault projects and secrets."""

import json
import os
from pathlib import Path

DEFAULT_VAULT_DIR = Path.home() / ".envault"
PROJECTS_FILE = "projects.json"


def get_vault_dir() -> Path:
    """Return the vault directory, creating it if necessary."""
    vault_dir = Path(os.environ.get("ENVAULT_DIR", DEFAULT_VAULT_DIR))
    vault_dir.mkdir(parents=True, exist_ok=True)
    return vault_dir


def load_projects() -> dict:
    """Load all registered projects from disk."""
    projects_path = get_vault_dir() / PROJECTS_FILE
    if not projects_path.exists():
        return {}
    with open(projects_path, "r") as f:
        return json.load(f)


def save_projects(projects: dict) -> None:
    """Persist all projects to disk."""
    projects_path = get_vault_dir() / PROJECTS_FILE
    with open(projects_path, "w") as f:
        json.dump(projects, f, indent=2)


def get_project_dir(project_name: str) -> Path:
    """Return the directory for a specific project."""
    project_dir = get_vault_dir() / "projects" / project_name
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def load_secrets(project_name: str) -> dict:
    """Load secrets for a given project."""
    secrets_path = get_project_dir(project_name) / "secrets.json"
    if not secrets_path.exists():
        return {}
    with open(secrets_path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Secrets file for project '{project_name}' is corrupted: {e}"
            ) from e


def save_secrets(project_name: str, secrets: dict) -> None:
    """Persist secrets for a given project."""
    secrets_path = get_project_dir(project_name) / "secrets.json"
    with open(secrets_path, "w") as f:
        json.dump(secrets, f, indent=2)


def delete_project(project_name: str) -> bool:
    """Remove a project's secrets file and directory from the vault.

    Returns True if the project directory existed and was removed,
    False if the project was not found.
    """
    import shutil

    project_dir = get_vault_dir() / "projects" / project_name
    if not project_dir.exists():
        return False
    shutil.rmtree(project_dir)
    return True
