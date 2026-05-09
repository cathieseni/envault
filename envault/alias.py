"""
envault.alias — Manage key aliases within a project.

Allows secrets to be referenced by alternate names, useful for
renaming keys without breaking existing consumers.
"""

from __future__ import annotations

import json
from pathlib import Path

from envault.storage import get_project_dir
from envault.secrets import get_secret


def _get_alias_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "aliases.json"


def _load_aliases(project_name: str) -> dict[str, str]:
    path = _get_alias_path(project_name)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_aliases(project_name: str, aliases: dict[str, str]) -> None:
    path = _get_alias_path(project_name)
    path.write_text(json.dumps(aliases, indent=2))


def add_alias(project_name: str, alias: str, target_key: str) -> None:
    """Register *alias* as an alternate name for *target_key*.

    Raises KeyError if *target_key* does not exist in the project.
    Raises ValueError if *alias* is already in use.
    """
    # Verify the target key exists (raises KeyError if not)
    get_secret(project_name, target_key)

    aliases = _load_aliases(project_name)
    if alias in aliases:
        raise ValueError(f"Alias '{alias}' already exists (points to '{aliases[alias]}')")
    aliases[alias] = target_key
    _save_aliases(project_name, aliases)


def remove_alias(project_name: str, alias: str) -> None:
    """Remove *alias* from the project.

    Raises KeyError if the alias does not exist.
    """
    aliases = _load_aliases(project_name)
    if alias not in aliases:
        raise KeyError(f"Alias '{alias}' not found")
    del aliases[alias]
    _save_aliases(project_name, aliases)


def resolve_alias(project_name: str, alias: str) -> str:
    """Return the target key for *alias*, or *alias* itself if not an alias."""
    aliases = _load_aliases(project_name)
    return aliases.get(alias, alias)


def get_via_alias(project_name: str, alias: str) -> str:
    """Retrieve the secret value referenced by *alias* (or a direct key)."""
    key = resolve_alias(project_name, alias)
    return get_secret(project_name, key)


def list_aliases(project_name: str) -> dict[str, str]:
    """Return a mapping of alias -> target_key for the project."""
    return dict(_load_aliases(project_name))
