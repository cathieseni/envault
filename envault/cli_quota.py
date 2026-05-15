"""CLI commands for managing per-project secret quotas."""

from __future__ import annotations

import argparse
import sys

from envault.project import get_project
from envault.quota import check_quota, clear_quota, get_quota, set_quota


def cmd_quota_set(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"Error: project '{args.project}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.limit < 1:
        print("Error: limit must be at least 1.", file=sys.stderr)
        sys.exit(1)

    set_quota(args.project, args.limit)
    print(f"Quota for '{args.project}' set to {args.limit} secrets.")


def cmd_quota_get(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"Error: project '{args.project}' not found.", file=sys.stderr)
        sys.exit(1)

    current, limit, ok = check_quota(args.project)
    status = "OK" if ok else "EXCEEDED"
    print(f"Project : {args.project}")
    print(f"Secrets : {current}")
    print(f"Limit   : {limit}")
    print(f"Status  : {status}")
    if not ok:
        sys.exit(2)


def cmd_quota_clear(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError:
        print(f"Error: project '{args.project}' not found.", file=sys.stderr)
        sys.exit(1)

    clear_quota(args.project)
    print(f"Quota for '{args.project}' cleared (default restored).")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-quota",
        description="Manage per-project secret quotas.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set quota limit for a project.")
    p_set.add_argument("project", help="Project name.")
    p_set.add_argument("limit", type=int, help="Maximum number of secrets.")
    p_set.set_defaults(func=cmd_quota_set)

    p_get = sub.add_parser("get", help="Show quota status for a project.")
    p_get.add_argument("project", help="Project name.")
    p_get.set_defaults(func=cmd_quota_get)

    p_clear = sub.add_parser("clear", help="Clear custom quota (revert to default).")
    p_clear.add_argument("project", help="Project name.")
    p_clear.set_defaults(func=cmd_quota_clear)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
