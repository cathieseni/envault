"""CLI interface for secret pinning."""

from __future__ import annotations

import argparse
import sys

from envault.pin import pin_secret, unpin_secret, list_pinned


def cmd_pin(args: argparse.Namespace) -> None:
    try:
        pin_secret(args.project, args.key)
        print(f"Pinned '{args.key}' in project '{args.project}'.")
    except (KeyError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_unpin(args: argparse.Namespace) -> None:
    try:
        unpin_secret(args.project, args.key)
        print(f"Unpinned '{args.key}' in project '{args.project}'.")
    except (KeyError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_pinned(args: argparse.Namespace) -> None:
    try:
        pins = list_pinned(args.project)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not pins:
        print(f"No pinned secrets in project '{args.project}'.")
    else:
        for key in pins:
            print(key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-pin",
        description="Pin or unpin secrets to prevent rotation/overwrite.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pin = sub.add_parser("pin", help="Pin a secret key.")
    p_pin.add_argument("project", help="Project name.")
    p_pin.add_argument("key", help="Secret key to pin.")
    p_pin.set_defaults(func=cmd_pin)

    p_unpin = sub.add_parser("unpin", help="Unpin a secret key.")
    p_unpin.add_argument("project", help="Project name.")
    p_unpin.add_argument("key", help="Secret key to unpin.")
    p_unpin.set_defaults(func=cmd_unpin)

    p_list = sub.add_parser("list", help="List pinned secrets.")
    p_list.add_argument("project", help="Project name.")
    p_list.set_defaults(func=cmd_list_pinned)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
