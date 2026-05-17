"""CLI commands for secret grouping."""

from __future__ import annotations

import argparse
import sys

from envault.grouping import (
    add_to_group,
    remove_from_group,
    list_groups,
    get_group_members,
    delete_group,
    groups_for_key,
)


def cmd_group_add(args: argparse.Namespace) -> None:
    try:
        add_to_group(args.project, args.group, args.key)
        print(f"Added '{args.key}' to group '{args.group}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_group_remove(args: argparse.Namespace) -> None:
    try:
        remove_from_group(args.project, args.group, args.key)
        print(f"Removed '{args.key}' from group '{args.group}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_group_list(args: argparse.Namespace) -> None:
    groups = list_groups(args.project)
    if not groups:
        print("No groups defined.")
    else:
        for g in groups:
            print(g)


def cmd_group_members(args: argparse.Namespace) -> None:
    members = get_group_members(args.project, args.group)
    if not members:
        print(f"Group '{args.group}' is empty or does not exist.")
    else:
        for m in members:
            print(m)


def cmd_group_delete(args: argparse.Namespace) -> None:
    try:
        delete_group(args.project, args.group)
        print(f"Deleted group '{args.group}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_group_of_key(args: argparse.Namespace) -> None:
    groups = groups_for_key(args.project, args.key)
    if not groups:
        print(f"Key '{args.key}' belongs to no groups.")
    else:
        for g in groups:
            print(g)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-group", description="Manage secret groups")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd, fn, extra in [
        ("add", cmd_group_add, [("group",), ("key",)]),
        ("remove", cmd_group_remove, [("group",), ("key",)]),
        ("members", cmd_group_members, [("group",)]),
        ("delete", cmd_group_delete, [("group",)]),
        ("of-key", cmd_group_of_key, [("key",)]),
        ("list", cmd_group_list, []),
    ]:
        p = sub.add_parser(cmd)
        p.add_argument("project")
        for pos in extra:
            p.add_argument(*pos)
        p.set_defaults(func=fn)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
