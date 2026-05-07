"""Environment health check: verify required secrets exist and are non-expired."""

from typing import Optional
from envault.secrets import list_secrets, get_secret
from envault.expiry import get_expiry, is_expired
from envault.project import get_project


class CheckResult:
    def __init__(self, key: str, status: str, message: str):
        self.key = key
        self.status = status  # 'ok', 'missing', 'expired', 'expiring_soon'
        self.message = message

    def __repr__(self):
        return f"CheckResult(key={self.key!r}, status={self.status!r}, message={self.message!r})"


def check_project(
    project_name: str,
    required_keys: Optional[list] = None,
    warn_days: int = 7,
) -> list:
    """
    Check all (or specified) secrets for a project.

    - Verifies each required key exists.
    - Flags expired secrets.
    - Warns about secrets expiring within `warn_days` days.

    Returns a list of CheckResult objects.
    """
    get_project(project_name)  # raises KeyError if not found
    existing_keys = set(list_secrets(project_name))
    keys_to_check = required_keys if required_keys is not None else list(existing_keys)
    results = []

    for key in keys_to_check:
        if key not in existing_keys:
            results.append(CheckResult(key, "missing", f"Secret '{key}' is not set."))
            continue

        expiry_ts = get_expiry(project_name, key)
        if expiry_ts is None:
            results.append(CheckResult(key, "ok", f"Secret '{key}' is present and has no expiry."))
            continue

        if is_expired(project_name, key):
            results.append(CheckResult(key, "expired", f"Secret '{key}' has expired."))
            continue

        import time
        remaining_days = (expiry_ts - time.time()) / 86400
        if remaining_days <= warn_days:
            results.append(
                CheckResult(
                    key,
                    "expiring_soon",
                    f"Secret '{key}' expires in {remaining_days:.1f} day(s).",
                )
            )
        else:
            results.append(CheckResult(key, "ok", f"Secret '{key}' is present and valid."))

    return results


def has_issues(results: list) -> bool:
    """Return True if any result is not 'ok'."""
    return any(r.status != "ok" for r in results)
