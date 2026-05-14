"""Namespace support: group secrets under logical namespaces within a project."""

from envault.storage import get_project_dir, load_secrets, save_secrets
from envault.project import get_project

NAMESPACE_SEP = ":"


def _qualify(namespace: str, key: str) -> str:
    """Return a fully-qualified key: 'namespace:key'."""
    return f"{namespace}{NAMESPACE_SEP}{key}"


def set_in_namespace(project_name: str, namespace: str, key: str, value: str) -> str:
    """Store *value* under namespace:key in *project_name*.

    Returns the fully-qualified key that was written.
    """
    get_project(project_name)  # raises if missing
    from envault.secrets import set_secret
    fqk = _qualify(namespace, key)
    set_secret(project_name, fqk, value)
    return fqk


def get_in_namespace(project_name: str, namespace: str, key: str) -> str:
    """Retrieve the secret stored under namespace:key."""
    get_project(project_name)
    from envault.secrets import get_secret
    return get_secret(project_name, _qualify(namespace, key))


def list_namespace(project_name: str, namespace: str) -> dict:
    """Return a dict of {bare_key: value} for all keys in *namespace*."""
    get_project(project_name)
    from envault.secrets import list_secrets
    all_secrets = list_secrets(project_name)
    prefix = namespace + NAMESPACE_SEP
    return {
        k[len(prefix):]: v
        for k, v in all_secrets.items()
        if k.startswith(prefix)
    }


def delete_namespace(project_name: str, namespace: str) -> list:
    """Delete every secret that belongs to *namespace*.

    Returns the list of fully-qualified keys that were removed.
    """
    get_project(project_name)
    from envault.secrets import delete_secret, list_secrets
    all_secrets = list_secrets(project_name)
    prefix = namespace + NAMESPACE_SEP
    removed = [k for k in all_secrets if k.startswith(prefix)]
    for fqk in removed:
        delete_secret(project_name, fqk)
    return removed


def list_namespaces(project_name: str) -> list:
    """Return a sorted list of distinct namespace names used in *project_name*."""
    get_project(project_name)
    from envault.secrets import list_secrets
    names = set()
    for k in list_secrets(project_name):
        if NAMESPACE_SEP in k:
            names.add(k.split(NAMESPACE_SEP, 1)[0])
    return sorted(names)
