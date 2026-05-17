"""Synopsis module: generate a human-readable summary report for a project."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.project import get_project
from envault.secrets import list_secrets, get_secret
from envault.tag import list_tags
from envault.expiry import get_expiry, is_expired
from envault.lock import is_locked
from envault.pin import is_pinned
from envault.scoring import score_value


@dataclass
class SecretSummary:
    key: str
    locked: bool
    pinned: bool
    tags: List[str]
    expired: bool
    expiry_ts: Optional[float]
    score: int


@dataclass
class ProjectSynopsis:
    project_name: str
    total_secrets: int
    locked_count: int
    pinned_count: int
    expired_count: int
    avg_score: float
    secrets: List[SecretSummary] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Project : {self.project_name}",
            f"Secrets : {self.total_secrets}",
            f"Locked  : {self.locked_count}",
            f"Pinned  : {self.pinned_count}",
            f"Expired : {self.expired_count}",
            f"Avg score: {self.avg_score:.1f}/100",
        ]
        return "\n".join(lines)


def generate_synopsis(project_name: str) -> ProjectSynopsis:
    """Build a full synopsis for *project_name*."""
    get_project(project_name)  # raises KeyError if missing

    keys = list_secrets(project_name)
    secret_summaries: List[SecretSummary] = []

    for key in keys:
        value = get_secret(project_name, key)
        tags = list_tags(project_name, key)
        expiry_entry = get_expiry(project_name, key)
        expiry_ts = expiry_entry["expires_at"] if expiry_entry else None
        expired = is_expired(project_name, key) if expiry_entry else False
        locked = is_locked(project_name, key)
        pinned = is_pinned(project_name, key)
        score = score_value(value).score

        secret_summaries.append(
            SecretSummary(
                key=key,
                locked=locked,
                pinned=pinned,
                tags=tags,
                expired=expired,
                expiry_ts=expiry_ts,
                score=score,
            )
        )

    total = len(secret_summaries)
    locked_count = sum(1 for s in secret_summaries if s.locked)
    pinned_count = sum(1 for s in secret_summaries if s.pinned)
    expired_count = sum(1 for s in secret_summaries if s.expired)
    avg_score = (
        sum(s.score for s in secret_summaries) / total if total else 0.0
    )

    return ProjectSynopsis(
        project_name=project_name,
        total_secrets=total,
        locked_count=locked_count,
        pinned_count=pinned_count,
        expired_count=expired_count,
        avg_score=avg_score,
        secrets=secret_summaries,
    )
