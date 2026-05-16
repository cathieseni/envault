"""Secret strength scoring for envault projects."""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List

from envault.secrets import list_secrets, get_secret
from envault.project import get_project


@dataclass
class ScoreResult:
    key: str
    score: int          # 0-100
    grade: str          # A, B, C, D, F
    issues: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"<ScoreResult key={self.key!r} grade={self.grade} score={self.score}>"


_COMMON_WEAK = {"password", "secret", "123456", "qwerty", "admin", "changeme", "test"}


def _entropy(value: str) -> float:
    """Shannon entropy in bits per character."""
    if not value:
        return 0.0
    freq = {}
    for ch in value:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(value)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def score_value(key: str, value: str) -> ScoreResult:
    """Compute a strength score (0-100) for a single secret value."""
    issues: List[str] = []
    score = 100

    if not value:
        return ScoreResult(key=key, score=0, grade="F", issues=["empty value"])

    # Length penalties
    if len(value) < 8:
        score -= 40
        issues.append("too short (< 8 chars)")
    elif len(value) < 16:
        score -= 20
        issues.append("short (< 16 chars)")

    # Common weak values
    if value.lower() in _COMMON_WEAK:
        score -= 40
        issues.append("common/weak value")

    # Low entropy
    ent = _entropy(value)
    if ent < 2.0:
        score -= 30
        issues.append(f"low entropy ({ent:.2f} bits/char)")
    elif ent < 3.5:
        score -= 10
        issues.append(f"moderate entropy ({ent:.2f} bits/char)")

    # No character variety
    has_upper = bool(re.search(r"[A-Z]", value))
    has_digit = bool(re.search(r"[0-9]", value))
    has_special = bool(re.search(r"[^A-Za-z0-9]", value))
    variety = sum([has_upper, has_digit, has_special])
    if variety == 0:
        score -= 10
        issues.append("no uppercase, digits, or special characters")
    elif variety == 1:
        score -= 5
        issues.append("low character variety")

    score = max(0, min(100, score))
    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D" if score >= 35 else "F"
    return ScoreResult(key=key, score=score, grade=grade, issues=issues)


def score_project(project_name: str) -> Dict[str, ScoreResult]:
    """Score all secrets in a project. Returns a dict keyed by secret name."""
    get_project(project_name)  # raises KeyError if missing
    keys = list_secrets(project_name)
    results: Dict[str, ScoreResult] = {}
    for key in keys:
        value = get_secret(project_name, key)
        results[key] = score_value(key, value)
    return results
