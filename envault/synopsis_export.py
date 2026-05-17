"""Export a project synopsis to JSON or plain text."""

from __future__ import annotations

import json
from typing import Literal

from envault.synopsis import ProjectSynopsis, generate_synopsis


OutputFormat = Literal["text", "json"]


def _synopsis_to_dict(syn: ProjectSynopsis) -> dict:
    return {
        "project": syn.project_name,
        "total_secrets": syn.total_secrets,
        "locked_count": syn.locked_count,
        "pinned_count": syn.pinned_count,
        "expired_count": syn.expired_count,
        "avg_score": round(syn.avg_score, 2),
        "secrets": [
            {
                "key": s.key,
                "locked": s.locked,
                "pinned": s.pinned,
                "tags": s.tags,
                "expired": s.expired,
                "expiry_ts": s.expiry_ts,
                "score": s.score,
            }
            for s in syn.secrets
        ],
    }


def export_synopsis(
    project_name: str,
    fmt: OutputFormat = "text",
) -> str:
    """Return the synopsis for *project_name* as a formatted string.

    Parameters
    ----------
    project_name:
        The project to summarise.
    fmt:
        ``"text"`` (default) returns the human-readable summary;
        ``"json"`` returns a JSON-encoded object.
    """
    syn = generate_synopsis(project_name)

    if fmt == "json":
        return json.dumps(_synopsis_to_dict(syn), indent=2)

    # plain text — full detail
    lines = [syn.summary(), ""]
    for s in syn.secrets:
        tags_str = ",".join(s.tags) if s.tags else "-"
        flags = []
        if s.locked:
            flags.append("locked")
        if s.pinned:
            flags.append("pinned")
        if s.expired:
            flags.append("EXPIRED")
        flag_str = "[" + ",".join(flags) + "]" if flags else ""
        lines.append(f"  {s.key:<30} score={s.score:>3}  tags={tags_str}  {flag_str}")
    return "\n".join(lines)
