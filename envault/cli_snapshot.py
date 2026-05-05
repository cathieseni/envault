"""CLI sub-commands for snapshot management."""

import argparse
import sys

from envault.snapshot import create_snapshot, list_snapshots, restore_snapshot, delete_snapshot


def cmd_snapshot_create(args: argparse.Namespace) -> None:
    filename = create_snapshot(args.project, label=args.label)
    print(f"Snapshot created: {filename}")


def cmd_snapshot_list(args: argparse.Namespace) -> None:
    entries = list_snapshots(args.project)
    if not entries:
        print("No snapshots found.")
        return
    print(f"{'FILENAME':<40} {'TIMESTAMP':<18} {'SECRETS':>7}  LABEL")
    print("-" * 75)
    for e in entries:
        label = e["label"] or ""
        print(f"{e['filename']:<40} {e['timestamp']:<18} {e['secret_count']:>7}  {label}")


def cmd_snapshot_restore(args: argparse.Namespace) -> None:
    try:
        count = restore_snapshot(args.project, args.filename)
        print(f"Restored {count} secret(s) from '{args.filename}'.")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_snapshot_delete(args: argparse.Namespace) -> None:
    try:
        delete_snapshot(args.project, args.filename)
        print(f"Snapshot '{args.filename}' deleted.")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-snapshot", description="Manage secret snapshots")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Create a snapshot of current secrets")
    p_create.add_argument("project")
    p_create.add_argument("--label", default=None, help="Optional human-readable label")
    p_create.set_defaults(func=cmd_snapshot_create)

    p_list = sub.add_parser("list", help="List available snapshots")
    p_list.add_argument("project")
    p_list.set_defaults(func=cmd_snapshot_list)

    p_restore = sub.add_parser("restore", help="Restore secrets from a snapshot")
    p_restore.add_argument("project")
    p_restore.add_argument("filename", help="Snapshot filename to restore")
    p_restore.set_defaults(func=cmd_snapshot_restore)

    p_delete = sub.add_parser("delete", help="Delete a snapshot")
    p_delete.add_argument("project")
    p_delete.add_argument("filename", help="Snapshot filename to delete")
    p_delete.set_defaults(func=cmd_snapshot_delete)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
