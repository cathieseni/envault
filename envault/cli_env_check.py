"""CLI interface for the environment health check feature."""

import argparse
import sys
from envault.env_check import check_project, has_issues


def cmd_check(args):
    required_keys = args.keys if args.keys else None
    try:
        results = check_project(
            args.project,
            required_keys=required_keys,
            warn_days=args.warn_days,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No secrets to check.")
        sys.exit(0)

    status_icons = {
        "ok": "✓",
        "missing": "✗",
        "expired": "!",
        "expiring_soon": "~",
    }

    for r in results:
        icon = status_icons.get(r.status, "?")
        print(f"  [{icon}] {r.message}")

    if has_issues(results):
        sys.exit(1)
    else:
        sys.exit(0)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="envault-check",
        description="Check health of secrets for a project.",
    )
    parser.add_argument("project", help="Project name to check.")
    parser.add_argument(
        "--keys",
        nargs="+",
        metavar="KEY",
        help="Specific keys to verify (default: all secrets).",
    )
    parser.add_argument(
        "--warn-days",
        type=int,
        default=7,
        metavar="DAYS",
        help="Warn if a secret expires within this many days (default: 7).",
    )
    parser.set_defaults(func=cmd_check)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
