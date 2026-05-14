"""Cross-project secret key comparison utilities."""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from envault.project import get_project
from envault.secrets import list_secrets


@dataclass
class CompareResult:
    source: str
    target: str
    only_in_source: List[str] = field(default_factory=list)
    only_in_target: List[str] = field(default_factory=list)
    in_both: List[str] = field(default_factory=list)

    def has_differences(self) -> bool:
        return bool(self.only_in_source or self.only_in_target)

    def summary(self) -> Dict[str, int]:
        return {
            "only_in_source": len(self.only_in_source),
            "only_in_target": len(self.only_in_target),
            "in_both": len(self.in_both),
        }


def compare_projects(source_name: str, target_name: str) -> CompareResult:
    """Compare secret keys between two projects."""
    get_project(source_name)  # raises if not found
    get_project(target_name)  # raises if not found

    source_keys: Set[str] = set(list_secrets(source_name))
    target_keys: Set[str] = set(list_secrets(target_name))

    return CompareResult(
        source=source_name,
        target=target_name,
        only_in_source=sorted(source_keys - target_keys),
        only_in_target=sorted(target_keys - source_keys),
        in_both=sorted(source_keys & target_keys),
    )


def compare_many(base: str, others: List[str]) -> List[CompareResult]:
    """Compare a base project against multiple target projects."""
    return [compare_projects(base, other) for other in others]
