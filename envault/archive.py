"""Archive (soft-delete) and restore projects in envault."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from envault.storage import get_vault_dir, load_projects, save_projects


def _get_archive_dir() -> Path:
    archive_dir = get_vault_dir() / ".archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    return archive_dir


def archive_project(name: str) -> Path:
    """Move a project to the archive. Returns the archive path."""
    projects = load_projects()
    if name not in projects:
        raise KeyError(f"Project '{name}' not found.")

    vault_dir = get_vault_dir()
    project_dir = vault_dir / name
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory for '{name}' does not exist.")

    timestamp = int(time.time())
    archive_name = f"{name}__{timestamp}"
    dest = _get_archive_dir() / archive_name
    shutil.copytree(str(project_dir), str(dest))

    # Remove from active projects
    shutil.rmtree(str(project_dir))
    del projects[name]
    save_projects(projects)

    return dest


def list_archived() -> list[dict]:
    """Return a list of archived project entries with name and timestamp."""
    archive_dir = _get_archive_dir()
    entries = []
    for path in sorted(archive_dir.iterdir()):
        if path.is_dir() and "__" in path.name:
            parts = path.name.rsplit("__", 1)
            entries.append({
                "name": parts[0],
                "timestamp": int(parts[1]),
                "archive_name": path.name,
            })
    return entries


def restore_project(archive_name: str, overwrite: bool = False) -> str:
    """Restore an archived project back to active. Returns the project name."""
    archive_dir = _get_archive_dir()
    src = archive_dir / archive_name
    if not src.exists():
        raise FileNotFoundError(f"Archived project '{archive_name}' not found.")

    if "__" not in archive_name:
        raise ValueError(f"Invalid archive name format: '{archive_name}'.")

    project_name = archive_name.rsplit("__", 1)[0]
    projects = load_projects()

    if project_name in projects and not overwrite:
        raise ValueError(
            f"Project '{project_name}' already exists. Use overwrite=True to replace."
        )

    vault_dir = get_vault_dir()
    dest = vault_dir / project_name
    if dest.exists():
        shutil.rmtree(str(dest))

    shutil.copytree(str(src), str(dest))
    shutil.rmtree(str(src))

    projects[project_name] = {"name": project_name}
    save_projects(projects)

    return project_name


def delete_archived(archive_name: str) -> None:
    """Permanently delete an archived project."""
    archive_dir = _get_archive_dir()
    target = archive_dir / archive_name
    if not target.exists():
        raise FileNotFoundError(f"Archived project '{archive_name}' not found.")
    shutil.rmtree(str(target))
