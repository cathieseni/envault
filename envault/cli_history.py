"""CLI commands for viewing per-secret history in envault."""

import argparse
import sys
import time
from datetime import datetime

from envault.history import get_history, clear_history, all_history
from envault.project import get_project


def _fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def cmd_history_show(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        entries = get_history(args.project, args.key)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not entries:
        print(f"No history for '{args.key}'.")
        return

    print(f"History for '{args.key}' in project '{args.project}':")
    for i, entry in enumerate(reversed(entries), 1):
        ts = _fmt_ts(entry["timestamp"])
        actor = entry.get("actor", "unknown")
        old = entry.get("old_value", "")
        new = entry.get("new_value", "")
        print(f"  [{i}] {ts}  actor={actor}  {old!r} -> {new!r}")


def cmd_history_clear(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    clear_history(args.project, args.key)
    print(f"Cleared history for '{args.key}' in project '{args.project}'.")


def cmd_history_all(args: argparse.Namespace) -> None:
    try:
        get_project(args.project)
    except KeyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    data = all_history(args.project)
    if not data:
        print(f"No history recorded for project '{args.project}'.")
        return
    for key, entries in sorted(data.items()):
        print(f"  {key}: {len(entries)} change(s)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-history", description="Secret history commands")
    sub = parser.add_subparsers(dest="command", required=True)

    p_show = sub.add_parser("show", help="Show change history for a key")
    p_show.add_argument("project")
    p_show.add_argument("key")
    p_show.set_defaults(func=cmd_history_show)

    p_clear = sub.add_parser("clear", help="Clear history for a key")
    p_clear.add_argument("project")
    p_clear.add_argument("key")
    p_clear.set_defaults(func=cmd_history_clear)

    p_all = sub.add_parser("all", help="List all keys with recorded history")
    p_all.add_argument("project")
    p_all.set_defaults(func=cmd_history_all)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
