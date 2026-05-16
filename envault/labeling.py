"""Per-secret label management for envault.

Labels are free-form key=value metadata attached to secrets,
distinct from tags (which are plain strings).
"""

import json
from pathlib import Path
from typing import Dict, Optional

from envault.storage import get_project_dir
from envault.secrets import list_secrets


def _get_label_path(project: str) -> Path:
    return get_project_dir(project) / "labels.json"


def _load_labels(project: str) -> Dict[str, Dict[str, str]]:
    path = _get_label_path(project)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_labels(project: str, data: Dict[str, Dict[str, str]]) -> None:
    path = _get_label_path(project)
    path.write_text(json.dumps(data, indent=2))


def set_label(project: str, key: str, label_key: str, label_value: str) -> None:
    """Attach a label (label_key=label_value) to a secret key."""
    existing_keys = list_secrets(project)
    if key not in existing_keys:
        raise KeyError(f"Secret '{key}' not found in project '{project}'")
    if not label_key or not label_key.isidentifier():
        raise ValueError(f"Label key '{label_key}' must be a valid identifier")
    data = _load_labels(project)
    data.setdefault(key, {})[label_key] = label_value
    _save_labels(project, data)


def remove_label(project: str, key: str, label_key: str) -> None:
    """Remove a single label from a secret key."""
    data = _load_labels(project)
    if key not in data or label_key not in data[key]:
        raise KeyError(f"Label '{label_key}' not found on secret '{key}'")
    del data[key][label_key]
    if not data[key]:
        del data[key]
    _save_labels(project, data)


def get_labels(project: str, key: str) -> Dict[str, str]:
    """Return all labels for a given secret key."""
    data = _load_labels(project)
    return dict(data.get(key, {}))


def find_by_label(
    project: str, label_key: str, label_value: Optional[str] = None
) -> Dict[str, Dict[str, str]]:
    """Return secrets whose labels match label_key (and optionally label_value)."""
    data = _load_labels(project)
    result = {}
    for secret_key, labels in data.items():
        if label_key in labels:
            if label_value is None or labels[label_key] == label_value:
                result[secret_key] = dict(labels)
    return result


def clear_labels(project: str, key: str) -> None:
    """Remove all labels from a secret key."""
    data = _load_labels(project)
    if key in data:
        del data[key]
        _save_labels(project, data)
