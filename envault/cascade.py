"""Cascade secret propagation across dependent projects."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.project import get_project
from envault.secrets import get_secret, set_secret, list_secrets
from envault.dependencies import list_dependencies
from envault.audit import log_event


@dataclass
class CascadeResult:
    source_project: str
    key: str
    propagated_to: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    def summary(self) -> str:
        lines = [
            f"Cascade '{self.key}' from '{self.source_project}'",
            f"  Propagated : {self.propagated_to or 'none'}",
            f"  Skipped    : {self.skipped or 'none'}",
        ]
        if self.errors:
            lines.append(f"  Errors     : {self.errors}")
        return "\n".join(lines)


def cascade_secret(
    source_project: str,
    key: str,
    targets: Optional[List[str]] = None,
    overwrite: bool = True,
) -> CascadeResult:
    """Propagate a secret value from source_project to target projects.

    If *targets* is None, targets are resolved from the source project's
    dependency list (projects that depend on source_project).
    """
    get_project(source_project)  # raises KeyError if missing
    value = get_secret(source_project, key)  # raises KeyError if missing

    if targets is None:
        targets = _find_dependents(source_project, key)

    result = CascadeResult(source_project=source_project, key=key)

    for target in targets:
        try:
            get_project(target)
        except KeyError:
            result.errors[target] = "project not found"
            continue

        if not overwrite:
            existing = list_secrets(target)
            if key in existing:
                result.skipped.append(target)
                continue

        try:
            set_secret(target, key, value)
            log_event(target, "cascade_receive", {"key": key, "from": source_project})
            result.propagated_to.append(target)
        except Exception as exc:  # pragma: no cover
            result.errors[target] = str(exc)

    log_event(
        source_project,
        "cascade_send",
        {"key": key, "targets": result.propagated_to},
    )
    return result


def _find_dependents(project_name: str, key: str) -> List[str]:
    """Return projects whose dependency list includes *project_name* for *key*."""
    from envault.project import list_projects

    dependents: List[str] = []
    for proj in list_projects():
        if proj == project_name:
            continue
        try:
            deps = list_dependencies(proj, key)
            if project_name in deps:
                dependents.append(proj)
        except Exception:
            pass
    return dependents
