import os
import json
import datetime
from cryptography.fernet import Fernet
from envault.storage import get_project_dir, load_secrets, save_secrets
from envault.project import get_project


def _get_or_create_key(project_name: str) -> bytes:
    project_dir = get_project_dir(project_name)
    key_path = os.path.join(project_dir, ".key")
    if os.path.exists(key_path):
        with open(key_path, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(key_path, "wb") as f:
        f.write(key)
    return key


def set_secret(project_name: str, key: str, value: str) -> None:
    get_project(project_name)  # raises if not found
    fernet = Fernet(_get_or_create_key(project_name))
    secrets = load_secrets(project_name)
    encrypted = fernet.encrypt(value.encode()).decode()
    secrets[key] = {
        "value": encrypted,
        "updated_at": datetime.datetime.utcnow().isoformat(),
    }
    save_secrets(project_name, secrets)


def get_secret(project_name: str, key: str) -> str:
    get_project(project_name)  # raises if not found
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    fernet = Fernet(_get_or_create_key(project_name))
    encrypted = secrets[key]["value"].encode()
    return fernet.decrypt(encrypted).decode()


def delete_secret(project_name: str, key: str) -> None:
    get_project(project_name)  # raises if not found
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    del secrets[key]
    save_secrets(project_name, secrets)


def list_secrets(project_name: str) -> list[dict]:
    get_project(project_name)  # raises if not found
    secrets = load_secrets(project_name)
    return [
        {"key": k, "updated_at": v.get("updated_at", "unknown")}
        for k, v in secrets.items()
    ]


def rotate_secret(project_name: str, key: str, new_value: str) -> None:
    """Rotate a secret to a new value (old value is overwritten)."""
    get_project(project_name)  # raises if not found
    secrets = load_secrets(project_name)
    if key not in secrets:
        raise KeyError(f"Secret '{key}' not found in project '{project_name}'.")
    set_secret(project_name, key, new_value)
