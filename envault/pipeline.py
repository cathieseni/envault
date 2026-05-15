"""Pipeline module: define and run ordered sequences of envault operations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from envault.storage import get_project_dir
from envault.project import get_project


def _get_pipeline_path(project_name: str) -> Path:
    return get_project_dir(project_name) / "pipelines.json"


def _load_pipelines(project_name: str) -> dict[str, list[dict]]:
    path = _get_pipeline_path(project_name)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_pipelines(project_name: str, data: dict[str, list[dict]]) -> None:
    path = _get_pipeline_path(project_name)
    path.write_text(json.dumps(data, indent=2))


def create_pipeline(project_name: str, pipeline_name: str, steps: list[dict[str, Any]]) -> None:
    """Create or replace a named pipeline with a list of step definitions."""
    get_project(project_name)  # raises if missing
    for step in steps:
        if "action" not in step:
            raise ValueError(f"Each step must have an 'action' key, got: {step}")
    data = _load_pipelines(project_name)
    data[pipeline_name] = steps
    _save_pipelines(project_name, data)


def get_pipeline(project_name: str, pipeline_name: str) -> list[dict[str, Any]]:
    """Return steps for a named pipeline."""
    get_project(project_name)
    data = _load_pipelines(project_name)
    if pipeline_name not in data:
        raise KeyError(f"Pipeline '{pipeline_name}' not found in project '{project_name}'")
    return data[pipeline_name]


def list_pipelines(project_name: str) -> list[str]:
    """Return all pipeline names for a project."""
    get_project(project_name)
    return list(_load_pipelines(project_name).keys())


def delete_pipeline(project_name: str, pipeline_name: str) -> None:
    """Delete a named pipeline."""
    get_project(project_name)
    data = _load_pipelines(project_name)
    if pipeline_name not in data:
        raise KeyError(f"Pipeline '{pipeline_name}' not found in project '{project_name}'")
    del data[pipeline_name]
    _save_pipelines(project_name, data)


def run_pipeline(project_name: str, pipeline_name: str) -> list[dict[str, Any]]:
    """Execute a pipeline and return a list of result records per step."""
    from envault.secrets import set_secret, get_secret, delete_secret
    from envault.rotation import rotate_secret

    steps = get_pipeline(project_name, pipeline_name)
    results = []
    for i, step in enumerate(steps):
        action = step["action"]
        try:
            if action == "set":
                set_secret(project_name, step["key"], step["value"])
                results.append({"step": i, "action": action, "status": "ok"})
            elif action == "get":
                value = get_secret(project_name, step["key"])
                results.append({"step": i, "action": action, "status": "ok", "value": value})
            elif action == "delete":
                delete_secret(project_name, step["key"])
                results.append({"step": i, "action": action, "status": "ok"})
            elif action == "rotate":
                old, new = rotate_secret(project_name, step["key"])
                results.append({"step": i, "action": action, "status": "ok", "old": old, "new": new})
            else:
                results.append({"step": i, "action": action, "status": "error", "error": f"Unknown action '{action}'"})
        except Exception as exc:
            results.append({"step": i, "action": action, "status": "error", "error": str(exc)})
    return results
