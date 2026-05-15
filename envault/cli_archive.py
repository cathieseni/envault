"""CLI commands for archiving and restoring envault projects."""

from __future__ import annotations

import argparse
import sys
import time

from envault.archive import (
    archive_project,
    delete_archived,
    list_archived,
    restore_project,
)


def cmd_archive(args: argparse.Namespace) -> None:
    try:
        dest = archive_project(args.project)
        print(f"Archived '{args.project}' -> {dest.name}")
    except (KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_archive_list(args: argparse.Namespace) -> None:
    entries = list_archived()
    if not entries:
        print("No archived projects.")
        return
    print(f"{'Archive Name':<40}  {'Original':<20}  Archived At")
    print("-" * 75)
    for e in entries:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e["timestamp"]))
        print(f"{e['archive_name']:<40}  {e['name']:<20}  {ts}")


def cmd_restore(args: argparse.Namespace) -> None:
    try:
        name = restore_project(args.archive_name, overwrite=args.overwrite)
        print(f"Restored '{args.archive_name}' as project '{name}'.")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_archive_delete(args: argparse.Namespace) -> None:
    try:
        delete_archived(args.archive_name)
        print(f"Permanently deleted archive '{args.archive_name}'.")
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-archive",
        description="Archive and restore envault projects.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_archive = sub.add_parser("archive", help="Archive (soft-delete) a project.")
    p_archive.add_argument("project", help="Project name to archive.")
    p_archive.set_defaults(func=cmd_archive)

    p_list = sub.add_parser("list", help="List archived projects.")
    p_list.set_defaults(func=cmd_archive_list)

    p_restore = sub.add_parser("restore", help="Restore an archived project.")
    p_restore.add_argument("archive_name", help="Archive entry name (e.g. myapp__1700000000).")
    p_restore.add_argument(
        "--overwrite", action="store_true", help="Overwrite if project already exists."
    )
    p_restore.set_defaults(func=cmd_restore)

    p_delete = sub.add_parser("delete", help="Permanently delete an archived project.")
    p_delete.add_argument("archive_name", help="Archive entry name to delete permanently.")
    p_delete.set_defaults(func=cmd_archive_delete)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
