"""Template rendering: inject secrets into .env.template files."""

import re
from pathlib import Path
from typing import Optional

from envault.secrets import get_secret, list_secrets
from envault.project import get_project

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")


def render_template(project_name: str, template_path: str, output_path: Optional[str] = None) -> str:
    """Render a template file by replacing {{KEY}} placeholders with secret values.

    Args:
        project_name: Registered project name.
        template_path: Path to the .env.template (or any text template) file.
        output_path: If given, write rendered content to this path.

    Returns:
        The rendered string.

    Raises:
        FileNotFoundError: If template_path does not exist.
        KeyError: If a placeholder key is not found in the project's secrets.
    """
    get_project(project_name)  # validates project exists

    src = Path(template_path)
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    content = src.read_text(encoding="utf-8")
    missing: list[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        try:
            return get_secret(project_name, key)
        except KeyError:
            missing.append(key)
            return match.group(0)  # leave placeholder intact for error reporting

    rendered = _PLACEHOLDER_RE.sub(_replace, content)

    if missing:
        raise KeyError(f"Missing secrets for placeholders: {', '.join(missing)}")

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")

    return rendered


def list_placeholders(template_path: str) -> list[str]:
    """Return all unique placeholder keys found in a template file."""
    src = Path(template_path)
    if not src.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    content = src.read_text(encoding="utf-8")
    seen: list[str] = []
    for match in _PLACEHOLDER_RE.finditer(content):
        key = match.group(1)
        if key not in seen:
            seen.append(key)
    return seen
