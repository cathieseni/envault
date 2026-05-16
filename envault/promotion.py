"""Promote secrets from one project to another (e.g. staging -> production)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.project import get_project
from envault.secrets import get_secret, set_secret, list_secrets
from envault.audit import log_event


@dataclass
class PromotionResult:
    source: str
    target: str
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    overwritten: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Promotion: {self.source} -> {self.target}",
            f"  Promoted  : {len(self.promoted)}",
            f"  Overwritten: {len(self.overwritten)}",
            f"  Skipped   : {len(self.skipped)}",
        ]
        return "\n".join(lines)


def promote_project(
    source: str,
    target: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    prefix: Optional[str] = None,
) -> PromotionResult:
    """Copy secrets from *source* project into *target* project.

    Args:
        source:    Name of the source project.
        target:    Name of the target project.
        keys:      Explicit list of keys to promote; defaults to all keys.
        overwrite: If True, existing keys in target are replaced.
        prefix:    Optional string prepended to each key name in target.
    """
    get_project(source)  # raises KeyError if missing
    get_project(target)

    all_keys = list_secrets(source)
    candidates = keys if keys is not None else all_keys

    # Validate requested keys exist in source
    missing = [k for k in candidates if k not in all_keys]
    if missing:
        raise KeyError(f"Keys not found in source project '{source}': {missing}")

    result = PromotionResult(source=source, target=target)
    target_keys = set(list_secrets(target))

    for key in candidates:
        dest_key = f"{prefix}{key}" if prefix else key
        value = get_secret(source, key)

        if dest_key in target_keys and not overwrite:
            result.skipped.append(dest_key)
            continue

        existed = dest_key in target_keys
        set_secret(target, dest_key, value)

        if existed:
            result.overwritten.append(dest_key)
        else:
            result.promoted.append(dest_key)

        log_event(
            target,
            "promote",
            {"key": dest_key, "source": source, "overwritten": existed},
        )

    return result
