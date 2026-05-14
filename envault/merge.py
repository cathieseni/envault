"""Merge secrets from one project into another with conflict resolution strategies."""

from typing import Literal, NamedTuple

from envault.project import get_project
from envault.secrets import list_secrets, get_secret, set_secret
from envault.lock import is_locked

ConflictStrategy = Literal["skip", "overwrite", "error"]


class MergeResult(NamedTuple):
    added: list[str]
    skipped: list[str]
    overwritten: list[str]
    errors: list[str]


def merge_projects(
    src_project: str,
    dst_project: str,
    conflict: ConflictStrategy = "skip",
    keys: list[str] | None = None,
) -> MergeResult:
    """Merge secrets from *src_project* into *dst_project*.

    Args:
        src_project: Name of the source project.
        dst_project: Name of the destination project.
        conflict: How to handle keys that already exist in the destination.
            - ``"skip"``      – leave the existing value untouched (default).
            - ``"overwrite"`` – replace the existing value with the source value.
            - ``"error"``     – abort and raise a ``ValueError`` on the first conflict.
        keys: Optional allowlist of secret keys to merge. When *None*, all
              secrets from the source project are merged.

    Returns:
        A :class:`MergeResult` summarising what happened.

    Raises:
        KeyError: If either project does not exist.
        ValueError: If *conflict* is ``"error"`` and a conflicting key is found,
                    or if a locked key in the destination would be overwritten.
    """
    get_project(src_project)  # raises KeyError if missing
    get_project(dst_project)  # raises KeyError if missing

    src_keys = list_secrets(src_project)
    if keys is not None:
        src_keys = [k for k in src_keys if k in keys]

    dst_keys = set(list_secrets(dst_project))

    added: list[str] = []
    skipped: list[str] = []
    overwritten: list[str] = []
    errors: list[str] = []

    for key in src_keys:
        if is_locked(dst_project, key):
            msg = f"Key '{key}' is locked in destination project '{dst_project}'"
            if conflict == "error":
                raise ValueError(msg)
            errors.append(key)
            continue

        value = get_secret(src_project, key)

        if key in dst_keys:
            if conflict == "skip":
                skipped.append(key)
                continue
            elif conflict == "error":
                raise ValueError(
                    f"Key '{key}' already exists in destination project '{dst_project}'"
                )
            # overwrite
            set_secret(dst_project, key, value)
            overwritten.append(key)
        else:
            set_secret(dst_project, key, value)
            added.append(key)

    return MergeResult(added=added, skipped=skipped, overwritten=overwritten, errors=errors)
