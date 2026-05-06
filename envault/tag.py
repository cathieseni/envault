"""Tag management for envault secrets — assign, list, and filter secrets by tag."""

from envault.storage import get_project_dir, load_secrets, save_secrets
from envault.audit import log_event


def add_tag(project_name: str, key: str, tag: str) -> None:
    """Add a tag to a secret."""
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    entry = secrets[key]
    tags = entry.get("tags", [])
    if tag not in tags:
        tags.append(tag)
        entry["tags"] = tags
        secrets[key] = entry
        save_secrets(project_name, secrets)
        log_event(project_name, "tag_add", {"key": key, "tag": tag})


def remove_tag(project_name: str, key: str, tag: str) -> None:
    """Remove a tag from a secret."""
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    entry = secrets[key]
    tags = entry.get("tags", [])
    if tag not in tags:
        raise ValueError(f"Tag '{tag}' not found on secret '{key}'.")
    tags.remove(tag)
    entry["tags"] = tags
    secrets[key] = entry
    save_secrets(project_name, secrets)
    log_event(project_name, "tag_remove", {"key": key, "tag": tag})


def list_tags(project_name: str, key: str) -> list[str]:
    """Return all tags for a given secret."""
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    return secrets[key].get("tags", [])


def get_secrets_by_tag(project_name: str, tag: str) -> dict[str, str]:
    """Return a mapping of key -> encrypted_value for secrets that have the given tag."""
    secrets = load_secrets(project_name)
    return {
        key: entry["value"]
        for key, entry in secrets.items()
        if tag in entry.get("tags", [])
    }


def all_tags(project_name: str) -> dict[str, list[str]]:
    """Return a mapping of key -> tags for all secrets in the project."""
    secrets = load_secrets(project_name)
    return {key: entry.get("tags", []) for key, entry in secrets.items()}
