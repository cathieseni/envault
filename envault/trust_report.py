"""Generate a trust coverage report for a project."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envault.secrets import list_secrets
from envault.trust import VALID_LEVELS, list_trust


@dataclass
class TrustReport:
    project: str
    total: int
    covered: int
    uncovered: List[str] = field(default_factory=list)
    by_level: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def coverage_pct(self) -> float:
        if self.total == 0:
            return 100.0
        return round(self.covered / self.total * 100, 1)

    def summary(self) -> str:
        lines = [
            f"Trust report for '{self.project}'",
            f"  Total secrets : {self.total}",
            f"  Covered       : {self.covered} ({self.coverage_pct}%)",
        ]
        for lvl in VALID_LEVELS:
            keys = self.by_level.get(lvl, [])
            if keys:
                lines.append(f"  {lvl:12s}: {', '.join(sorted(keys))}")
        if self.uncovered:
            lines.append(f"  uncovered     : {', '.join(sorted(self.uncovered))}")
        return "\n".join(lines)


def generate_report(project: str) -> TrustReport:
    """Build a TrustReport for the given project."""
    all_keys = list_secrets(project)
    trust_data = list_trust(project)

    by_level: Dict[str, List[str]] = {lvl: [] for lvl in VALID_LEVELS}
    covered = []
    uncovered = []

    for key in all_keys:
        if key in trust_data:
            lvl = trust_data[key]["level"]
            by_level.setdefault(lvl, []).append(key)
            covered.append(key)
        else:
            uncovered.append(key)

    return TrustReport(
        project=project,
        total=len(all_keys),
        covered=len(covered),
        uncovered=uncovered,
        by_level={k: v for k, v in by_level.items() if v},
    )
