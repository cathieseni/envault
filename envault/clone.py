"""Clone secrets from one project to another, optionally filtering by tag."""

from envault.project import get_project
from envault.secrets import list_secrets, get_secret, set_secret
from envault.tag import list_tags, add_tag
from envault.audit import log_event


def clone_project(
    src_project: str,
    dst_project: str,
    *,
    tag: str | None = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Clone secrets from *src_project* into *dst_project*.

    Args:
        src_project: Name of the source project.
        dst_project: Name of the destination project.
        tag: When given, only secrets that carry this tag are cloned.
        overwrite: If False (default) existing keys in dst are skipped.

    Returns:
        A mapping of {key: 'cloned' | 'skipped'} for every candidate key.
    """
    # Validate both projects exist
    get_project(src_project)
    get_project(dst_project)

    src_keys = list_secrets(src_project)

    if tag is not None:
        from envault.tag import get_secrets_by_tag
        tagged = set(get_secrets_by_tag(src_project, tag))
        src_keys = [k for k in src_keys if k in tagged]

    dst_keys = set(list_secrets(dst_project))
    report: dict[str, str] = {}

    for key in src_keys:
        if key in dst_keys and not overwrite:
            report[key] = "skipped"
            continue

        value = get_secret(src_project, key)
        set_secret(dst_project, key, value)

        # Mirror tags for the key
        for t in list_tags(src_project, key):
            try:
                add_tag(dst_project, key, t)
            except Exception:
                pass  # best-effort

        report[key] = "cloned"
        log_event(
            dst_project,
            "clone",
            {"key": key, "source": src_project, "overwrite": overwrite},
        )

    return report
