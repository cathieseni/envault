"""Import secrets from existing .env files into a vault project."""

import os
import re
from typing import Dict, Tuple

from envault.secrets import set_secret
from envault.audit import log_event


_DOTENV_LINE_RE = re.compile(
    r'^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$'
)


def parse_dotenv(content: str) -> Dict[str, str]:
    """Parse a .env file string and return a dict of key/value pairs."""
    result: Dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        match = _DOTENV_LINE_RE.match(stripped)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Strip inline comments (only when value is unquoted)
        if value and value[0] not in ('"', "'"):
            value = value.split('#')[0].strip()
        else:
            value = _strip_quotes(value)
        result[key] = value
    return result


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a value."""
    if len(value) >= 2:
        if (value[0] == '"' and value[-1] == '"') or \
           (value[0] == "'" and value[-1] == "'"):
            return value[1:-1]
    return value


def import_from_file(
    project_name: str,
    filepath: str,
    overwrite: bool = False,
) -> Tuple[int, int]:
    """Import secrets from a .env file into the named project.

    Returns a tuple of (imported_count, skipped_count).
    Raises FileNotFoundError if the file does not exist.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as fh:
        content = fh.read()

    pairs = parse_dotenv(content)
    imported = 0
    skipped = 0

    for key, value in pairs.items():
        try:
            existing = None
            from envault.secrets import get_secret
            try:
                existing = get_secret(project_name, key)
            except KeyError:
                existing = None

            if existing is not None and not overwrite:
                skipped += 1
                continue

            set_secret(project_name, key, value)
            imported += 1
        except Exception:
            skipped += 1

    log_event(project_name, "import", {"file": filepath, "imported": imported, "skipped": skipped})
    return imported, skipped
