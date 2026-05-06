"""CLI interface for tag management in envault."""

import argparse
import sys

from envault.tag import add_tag, remove_tag, list_tags, get_secrets_by_tag, all_tags
from envault.storage import get_vault_dir


def cmd_tag_add(args: argparse.Namespace) -> None:
    get_vault_dir()  # ensure vault exists
    try:
        add_tag(args.project, args.key, args.tag)
        print(f"Tag '{args.tag}' added to '{args.key}'.")
    except (KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_remove(args: argparse.Namespace) -> None:
    get_vault_dir()
    try:
        remove_tag(args.project, args.key, args.tag)
        print(f"Tag '{args.tag}' removed from '{args.key}'.")
    except (KeyError, ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_list(args: argparse.Namespace) -> None:
    get_vault_dir()
    try:
        if args.key:
            tags = list_tags(args.project, args.key)
            if tags:
                print("\n".join(tags))
            else:
                print(f"No tags on '{args.key}'.")
        else:
            mapping = all_tags(args.project)
            for key, tags in mapping.items():
                tag_str = ", ".join(tags) if tags else "(none)"
                print(f"{key}: {tag_str}")
    except (KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_filter(args: argparse.Namespace) -> None:
    get_vault_dir()
    try:
        matches = get_secrets_by_tag(args.project, args.tag)
        if matches:
            for key in matches:
                print(key)
        else:
            print(f"No secrets found with tag '{args.tag}'.")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-tag", description="Manage secret tags")
    sub = parser.add_subparsers(dest="command")

    for cmd_name in ("add", "remove"):
        p = sub.add_parser(cmd_name)
        p.add_argument("project")
        p.add_argument("key")
        p.add_argument("tag")

    p_list = sub.add_parser("list")
    p_list.add_argument("project")
    p_list.add_argument("key", nargs="?", default=None)

    p_filter = sub.add_parser("filter")
    p_filter.add_argument("project")
    p_filter.add_argument("tag")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {"add": cmd_tag_add, "remove": cmd_tag_remove,
                "list": cmd_tag_list, "filter": cmd_tag_filter}
    if args.command not in dispatch:
        parser.print_help()
        sys.exit(1)
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
