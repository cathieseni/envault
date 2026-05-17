"""CLI commands for managing retention policies."""

from __future__ import annotations

import argparse
import sys

from envault.retention import apply_retention, clear_retention, get_retention, set_retention
from envault.project import get_project


def cmd_retention_set(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"error: project '{args.project}' not found", file=sys.stderr)
        sys.exit(1)
    try:
        set_retention(args.project, args.days)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Retention policy set: {args.days} day(s) for project '{args.project}'")


def cmd_retention_get(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"error: project '{args.project}' not found", file=sys.stderr)
        sys.exit(1)
    days = get_retention(args.project)
    if days is None:
        print(f"No retention policy set for project '{args.project}'")
    else:
        print(f"{days}")


def cmd_retention_clear(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"error: project '{args.project}' not found", file=sys.stderr)
        sys.exit(1)
    clear_retention(args.project)
    print(f"Retention policy cleared for project '{args.project}'")


def cmd_retention_apply(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"error: project '{args.project}' not found", file=sys.stderr)
        sys.exit(1)
    purged = apply_retention(args.project)
    if purged:
        print(f"Purged {len(purged)} secret(s): {', '.join(purged)}")
    else:
        print("No secrets purged.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-retention", description="Manage secret retention policies")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set retention policy (max age in days)")
    p_set.add_argument("project")
    p_set.add_argument("days", type=int)
    p_set.set_defaults(func=cmd_retention_set)

    p_get = sub.add_parser("get", help="Show current retention policy")
    p_get.add_argument("project")
    p_get.set_defaults(func=cmd_retention_get)

    p_clear = sub.add_parser("clear", help="Remove retention policy")
    p_clear.add_argument("project")
    p_clear.set_defaults(func=cmd_retention_clear)

    p_apply = sub.add_parser("apply", help="Apply retention policy and purge old secrets")
    p_apply.add_argument("project")
    p_apply.set_defaults(func=cmd_retention_apply)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
