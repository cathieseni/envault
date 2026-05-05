"""Project management: register, list, and remove envault projects."""

from datetime import datetime, timezone
from pathlib import Path

from envault.storage import load_projects, save_projects, get_project_dir


def register_project(name: str, path: str) -> dict:
    """Register a new project with the given name and directory path."""
    projects = load_projects()
    if name in projects:
        raise ValueError(f"Project '{name}' already exists.")

    resolved = str(Path(path).resolve())
    project = {
        "name": name,
        "path": resolved,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    projects[name] = project
    save_projects(projects)
    return project


def list_projects() -> list[dict]:
    """Return a list of all registered projects."""
    return list(load_projects().values())


def get_project(name: str) -> dict:
    """Retrieve a single project by name."""
    projects = load_projects()
    if name not in projects:
        raise KeyError(f"Project '{name}' not found.")
    return projects[name]


def remove_project(name: str) -> None:
    """Remove a project and its associated vault data."""
    import shutil

    projects = load_projects()
    if name not in projects:
        raise KeyError(f"Project '{name}' not found.")

    del projects[name]
    save_projects(projects)

    project_dir = get_project_dir(name)
    if project_dir.exists():
        shutil.rmtree(project_dir)
