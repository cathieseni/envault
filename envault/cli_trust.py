"""CLI commands for managing secret trust levels."""

from __future__ import annotations

import argparse
import sys

from envault.trust import (
    VALID_LEVELS,
    get_by_level,
    get_trust,
    list_trust,
    remove_trust,
    set_trust,
)


def cmd_trust_set(args: argparse.Namespace) -> int:
    try:
        entry = set_trust(args.project, args.key, args.level, note=args.note or "")
        print(f"Set trust level '{entry['level']}' for '{args.key}' in '{args.project}'.")
        return 0
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def cmd_trust_get(args: argparse.Namespace) -> int:
    entry = get_trust(args.project, args.key)
    if entry is None:
        print(f"No trust entry for '{args.key}' in '{args.project}'.")
        return 1
    print(f"key={args.key}  level={entry['level']}  note={entry.get('note', '')}")
    return 0


def cmd_trust_remove(args: argparse.Namespace) -> int:
    removed = remove_trust(args.project, args.key)
    if removed:
        print(f"Removed trust entry for '{args.key}'.")
        return 0
    print(f"No trust entry found for '{args.key}'.")
    return 1


def cmd_trust_list(args: argparse.Namespace) -> int:
    entries = list_trust(args.project)
    if not entries:
        print(f"No trust entries for project '{args.project}'.")
        return 0
    for key, entry in sorted(entries.items()):
        note = f"  [{entry['note']}]" if entry.get("note") else ""
        print(f"  {key}: {entry['level']}{note}")
    return 0


def cmd_trust_filter(args: argparse.Namespace) -> int:
    try:
        entries = get_by_level(args.project, args.level)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    if not entries:
        print(f"No keys with trust level '{args.level}'.")
        return 0
    for key in sorted(entries):
        print(f"  {key}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-trust", description="Manage secret trust levels")
    sub = parser.add_subparsers(dest="command")

    p_set = sub.add_parser("set", help="Set trust level for a key")
    p_set.add_argument("project")
    p_set.add_argument("key")
    p_set.add_argument("level", choices=VALID_LEVELS)
    p_set.add_argument("--note", default="")
    p_set.set_defaults(func=cmd_trust_set)

    p_get = sub.add_parser("get", help="Get trust entry for a key")
    p_get.add_argument("project")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_trust_get)

    p_rm = sub.add_parser("remove", help="Remove trust entry for a key")
    p_rm.add_argument("project")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_trust_remove)

    p_ls = sub.add_parser("list", help="List all trust entries for a project")
    p_ls.add_argument("project")
    p_ls.set_defaults(func=cmd_trust_list)

    p_f = sub.add_parser("filter", help="Filter keys by trust level")
    p_f.add_argument("project")
    p_f.add_argument("level", choices=VALID_LEVELS)
    p_f.set_defaults(func=cmd_trust_filter)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
