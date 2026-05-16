"""CLI entry-point for the promotion feature."""

from __future__ import annotations

import argparse
import sys

from envault.promotion import promote_project


def cmd_promote(args: argparse.Namespace) -> None:
    keys = args.keys.split(",") if args.keys else None
    try:
        result = promote_project(
            source=args.source,
            target=args.target,
            keys=keys,
            overwrite=args.overwrite,
            prefix=args.prefix,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        for k in result.promoted:
            print(f"  + promoted  : {k}")
        for k in result.overwritten:
            print(f"  ~ overwritten: {k}")
        for k in result.skipped:
            print(f"  - skipped   : {k}")

    print(result.summary())

    if result.skipped and not args.overwrite:
        # Non-fatal: exit 2 to signal partial promotion
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-promote",
        description="Promote secrets from one project to another.",
    )
    parser.add_argument("source", help="Source project name")
    parser.add_argument("target", help="Target project name")
    parser.add_argument(
        "--keys",
        default=None,
        metavar="KEY1,KEY2",
        help="Comma-separated list of keys to promote (default: all)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing keys in target project",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        metavar="PREFIX",
        help="Prepend PREFIX to each key name in the target project",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print per-key promotion status",
    )
    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    cmd_promote(args)


if __name__ == "__main__":  # pragma: no cover
    main()
