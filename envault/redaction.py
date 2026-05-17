"""Redaction rules: mask secret values in output based on configurable patterns."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from envault.storage import get_project_dir

_REDACTION_FILE = "redaction.json"
_DEFAULT_MASK = "***"


def _get_redaction_path(project: str) -> Path:
    return get_project_dir(project) / _REDACTION_FILE


def _load_rules(project: str) -> Dict[str, dict]:
    path = _get_redaction_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_rules(project: str, rules: Dict[str, dict]) -> None:
    path = _get_redaction_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rules, indent=2))


def set_redaction_rule(
    project: str,
    key: str,
    *,
    mask: str = _DEFAULT_MASK,
    pattern: Optional[str] = None,
) -> None:
    """Register a redaction rule for *key*.

    If *pattern* is given (a regex), only portions of the value matching the
    pattern are masked; otherwise the entire value is replaced with *mask*.
    """
    from envault.secrets import list_secrets

    if key not in list_secrets(project):
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    rules = _load_rules(project)
    rules[key] = {"mask": mask, "pattern": pattern}
    _save_rules(project, rules)


def remove_redaction_rule(project: str, key: str) -> None:
    """Remove the redaction rule for *key*."""
    rules = _load_rules(project)
    if key not in rules:
        raise KeyError(f"No redaction rule for key '{key}' in project '{project}'")
    del rules[key]
    _save_rules(project, rules)


def get_redaction_rule(project: str, key: str) -> Optional[dict]:
    """Return the redaction rule for *key*, or None if none is set."""
    return _load_rules(project).get(key)


def list_redaction_rules(project: str) -> Dict[str, dict]:
    """Return all redaction rules for *project*."""
    return dict(_load_rules(project))


def redact(project: str, key: str, value: str) -> str:
    """Apply the redaction rule for *key* to *value*, returning the masked string.

    If no rule exists, *value* is returned unchanged.
    """
    rule = get_redaction_rule(project, key)
    if rule is None:
        return value
    mask = rule.get("mask", _DEFAULT_MASK)
    pattern = rule.get("pattern")
    if pattern:
        return re.sub(pattern, mask, value)
    return mask
