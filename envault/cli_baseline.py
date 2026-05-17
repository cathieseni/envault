"""CLI interface for baseline capture and drift detection."""

from __future__ import annotations

import argparse
import sys

from envault.baseline import capture_baseline, get_baseline, clear_baseline, diff_from_baseline
from envault.project import get_project


def cmd_baseline_capture(args: argparse.Namespace) -> None:
    get_project(args.project)  # raises if missing
    entry = capture_baseline(args.project)
    key_count = len(entry["secrets"])
    print(f"Baseline captured for '{args.project}' ({key_count} secret(s)).")


def cmd_baseline_show(args: argparse.Namespace) -> None:
    get_project(args.project)
    entry = get_baseline(args.project)
    if entry is None:
        print(f"No baseline set for '{args.project}'.")
        sys.exit(1)
    import datetime
    ts = datetime.datetime.fromtimestamp(entry["captured_at"]).isoformat()
    print(f"Baseline for '{args.project}' captured at {ts}:")
    for k in sorted(entry["secrets"]):
        print(f"  {k}")


def cmd_baseline_diff(args: argparse.Namespace) -> None:
    get_project(args.project)
    try:
        result = diff_from_baseline(args.project)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    has_drift = result["added"] or result["removed"] or result["changed"]
    for k in result["added"]:
        print(f"+ {k}")
    for k in result["removed"]:
        print(f"- {k}")
    for k in result["changed"]:
        print(f"~ {k}")
    for k in result["unchanged"]:
        print(f"  {k}")
    if has_drift:
        sys.exit(1)


def cmd_baseline_clear(args: argparse.Namespace) -> None:
    get_project(args.project)
    removed = clear_baseline(args.project)
    if removed:
        print(f"Baseline cleared for '{args.project}'.")
    else:
        print(f"No baseline found for '{args.project}'.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-baseline", description="Baseline drift detection")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd, func in [
        ("capture", cmd_baseline_capture),
        ("show", cmd_baseline_show),
        ("diff", cmd_baseline_diff),
        ("clear", cmd_baseline_clear),
    ]:
        p = sub.add_parser(cmd)
        p.add_argument("project")
        p.set_defaults(func=func)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
