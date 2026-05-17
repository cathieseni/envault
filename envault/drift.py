"""Drift detection: compare current secrets against a captured baseline snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.baseline import get_baseline
from envault.secrets import list_secrets, get_secret
from envault.project import get_project


@dataclass
class DriftResult:
    project: str
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = [f"Drift report for '{self.project}':"]
        if not self.has_drift:
            lines.append("  No drift detected.")
            return "\n".join(lines)
        for k in self.added:
            lines.append(f"  + {k}  (added)")
        for k in self.removed:
            lines.append(f"  - {k}  (removed)")
        for k in self.changed:
            lines.append(f"  ~ {k}  (changed)")
        return "\n".join(lines)


def detect_drift(project_name: str) -> DriftResult:
    """Compare current live secrets against the stored baseline.

    Raises KeyError if the project does not exist.
    Raises FileNotFoundError if no baseline has been captured.
    """
    get_project(project_name)  # validates existence

    baseline: Optional[Dict[str, str]] = get_baseline(project_name)
    if baseline is None:
        raise FileNotFoundError(
            f"No baseline captured for project '{project_name}'. "
            "Run 'envault baseline capture' first."
        )

    current_keys = set(list_secrets(project_name))
    baseline_keys = set(baseline.keys())

    added = sorted(current_keys - baseline_keys)
    removed = sorted(baseline_keys - current_keys)

    changed: List[str] = []
    unchanged: List[str] = []
    for key in sorted(current_keys & baseline_keys):
        current_val = get_secret(project_name, key)
        if current_val != baseline[key]:
            changed.append(key)
        else:
            unchanged.append(key)

    return DriftResult(
        project=project_name,
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )
