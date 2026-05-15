"""CLI for pipeline management."""
from __future__ import annotations

import argparse
import json
import sys

from envault.pipeline import (
    create_pipeline,
    get_pipeline,
    list_pipelines,
    delete_pipeline,
    run_pipeline,
)


def cmd_pipeline_create(args: argparse.Namespace) -> None:
    try:
        steps = json.loads(args.steps_json)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON for steps: {exc}", file=sys.stderr)
        sys.exit(1)
    try:
        create_pipeline(args.project, args.name, steps)
        print(f"Pipeline '{args.name}' created in project '{args.project}'.")
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pipeline_list(args: argparse.Namespace) -> None:
    try:
        names = list_pipelines(args.project)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    if not names:
        print("No pipelines defined.")
    else:
        for name in names:
            print(name)


def cmd_pipeline_show(args: argparse.Namespace) -> None:
    try:
        steps = get_pipeline(args.project, args.name)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(steps, indent=2))


def cmd_pipeline_delete(args: argparse.Namespace) -> None:
    try:
        delete_pipeline(args.project, args.name)
        print(f"Pipeline '{args.name}' deleted.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_pipeline_run(args: argparse.Namespace) -> None:
    try:
        results = run_pipeline(args.project, args.name)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    errors = [r for r in results if r["status"] == "error"]
    print(json.dumps(results, indent=2))
    if errors:
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-pipeline", description="Manage envault pipelines")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a pipeline")
    p_create.add_argument("project")
    p_create.add_argument("name")
    p_create.add_argument("steps_json", help='JSON array of step objects, e.g. [{"action":"set","key":"K","value":"V"}]')
    p_create.set_defaults(func=cmd_pipeline_create)

    p_list = sub.add_parser("list", help="List pipelines")
    p_list.add_argument("project")
    p_list.set_defaults(func=cmd_pipeline_list)

    p_show = sub.add_parser("show", help="Show pipeline steps")
    p_show.add_argument("project")
    p_show.add_argument("name")
    p_show.set_defaults(func=cmd_pipeline_show)

    p_delete = sub.add_parser("delete", help="Delete a pipeline")
    p_delete.add_argument("project")
    p_delete.add_argument("name")
    p_delete.set_defaults(func=cmd_pipeline_delete)

    p_run = sub.add_parser("run", help="Run a pipeline")
    p_run.add_argument("project")
    p_run.add_argument("name")
    p_run.set_defaults(func=cmd_pipeline_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
