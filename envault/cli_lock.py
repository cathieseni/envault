"""CLI commands for secret locking."""

from __future__ import annotations

import argparse
import sys

from envault.lock import lock_secret, unlock_secret, list_locked


def cmd_lock(args: argparse.Namespace) -> None:
    try:
        lock_secret(args.project, args.key)
        print(f"Locked '{args.key}' in project '{args.project}'.")
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unlock(args: argparse.Namespace) -> None:
    try:
        unlock_secret(args.project, args.key)
        print(f"Unlocked '{args.key}' in project '{args.project}'.")
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_locked(args: argparse.Namespace) -> None:
    try:
        keys = list_locked(args.project)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not keys:
        print(f"No locked secrets in project '{args.project}'.")
    else:
        for k in keys:
            print(k)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage secret locks")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lock = sub.add_parser("lock", help="Lock a secret key")
    p_lock.add_argument("project")
    p_lock.add_argument("key")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = sub.add_parser("unlock", help="Unlock a secret key")
    p_unlock.add_argument("project")
    p_unlock.add_argument("key")
    p_unlock.set_defaults(func=cmd_unlock)

    p_list = sub.add_parser("list", help="List locked keys")
    p_list.add_argument("project")
    p_list.set_defaults(func=cmd_list_locked)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
