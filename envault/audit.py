import os
import json
import datetime
from envault.storage import get_project_dir

AUDIT_FILE = "audit.log"


def _get_audit_path(project_name: str) -> str:
    return os.path.join(get_project_dir(project_name), AUDIT_FILE)


def log_event(project_name: str, action: str, key: str, actor: str = "cli") -> None:
    audit_path = _get_audit_path(project_name)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "project": project_name,
        "action": action,
        "key": key,
        "actor": actor,
    }
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_audit_log(project_name: str) -> list[dict]:
    audit_path = _get_audit_path(project_name)
    if not os.path.exists(audit_path):
        return []
    entries = []
    with open(audit_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def clear_audit_log(project_name: str) -> None:
    audit_path = _get_audit_path(project_name)
    if os.path.exists(audit_path):
        os.remove(audit_path)
