"""Export secrets to various formats (.env, JSON, shell export statements)."""

import json
from typing import Literal

from envault.project import get_project
from envault.secrets import list_secrets, get_secret
from envault.audit import log_event

ExportFormat = Literal["dotenv", "json", "shell"]


def export_secrets(
    project_name: str,
    fmt: ExportFormat = "dotenv",
    redact: bool = False,
) -> str:
    """Return secrets for *project_name* serialised in the requested format.

    Args:
        project_name: Registered project name.
        fmt: One of ``dotenv``, ``json``, or ``shell``.
        redact: If *True* replace values with ``***`` (useful for logging).

    Returns:
        A string ready to be written to a file or printed to stdout.
    """
    get_project(project_name)  # raises KeyError if not found

    keys = list_secrets(project_name)
    pairs: dict[str, str] = {}
    for key in keys:
        value = get_secret(project_name, key)
        pairs[key] = "***" if redact else value

    log_event(project_name, "export", {"format": fmt, "redacted": redact, "keys": keys})

    if fmt == "dotenv":
        return _to_dotenv(pairs)
    elif fmt == "json":
        return _to_json(pairs)
    elif fmt == "shell":
        return _to_shell(pairs)
    else:
        raise ValueError(f"Unknown export format: {fmt!r}")


def _to_dotenv(pairs: dict[str, str]) -> str:
    lines = []
    for key, value in pairs.items():
        escaped = value.replace('"', '\\"')
        lines.append(f'{key}="{escaped}"')
    return "\n".join(lines)


def _to_json(pairs: dict[str, str]) -> str:
    return json.dumps(pairs, indent=2)


def _to_shell(pairs: dict[str, str]) -> str:
    lines = []
    for key, value in pairs.items():
        escaped = value.replace("'", "'\"'\"'")
        lines.append(f"export {key}='{escaped}'")
    return "\n".join(lines)
