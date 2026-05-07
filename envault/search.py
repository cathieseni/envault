"""Search secrets across projects by key name, value pattern, or tag."""

import fnmatch
from typing import Optional

from envault.storage import load_projects
from envault.secrets import list_secrets, get_secret
from envault.tag import list_tags


def search_by_key(
    pattern: str,
    project_name: Optional[str] = None,
) -> list[dict]:
    """Search for secrets whose key matches a glob pattern.

    Returns a list of dicts: {project, key, value}.
    If project_name is given, only that project is searched.
    """
    results = []
    projects = _resolve_projects(project_name)
    for proj in projects:
        for key in list_secrets(proj):
            if fnmatch.fnmatch(key, pattern):
                results.append({
                    "project": proj,
                    "key": key,
                    "value": get_secret(proj, key),
                })
    return results


def search_by_value(
    pattern: str,
    project_name: Optional[str] = None,
) -> list[dict]:
    """Search for secrets whose value matches a glob pattern.

    Returns a list of dicts: {project, key, value}.
    """
    results = []
    projects = _resolve_projects(project_name)
    for proj in projects:
        for key in list_secrets(proj):
            value = get_secret(proj, key)
            if fnmatch.fnmatch(value, pattern):
                results.append({
                    "project": proj,
                    "key": key,
                    "value": value,
                })
    return results


def search_by_tag(
    tag: str,
    project_name: Optional[str] = None,
) -> list[dict]:
    """Return all secrets that carry the given tag.

    Returns a list of dicts: {project, key, value, tags}.
    """
    results = []
    projects = _resolve_projects(project_name)
    for proj in projects:
        for key in list_secrets(proj):
            tags = list_tags(proj, key)
            if tag in tags:
                results.append({
                    "project": proj,
                    "key": key,
                    "value": get_secret(proj, key),
                    "tags": tags,
                })
    return results


def _resolve_projects(project_name: Optional[str]) -> list[str]:
    if project_name:
        return [project_name]
    projects = load_projects()
    return list(projects.keys())
