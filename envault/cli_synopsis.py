"""CLI entry-point for the synopsis feature."""

from __future__ import annotations

import argparse
import sys

from envault.synopsis import generate_synopsis


def cmd_synopsis(args: argparse.Namespace) -> None:
    try:
        syn = generate_synopsis(args.project)
    except KeyError:
        print(f"error: project '{args.project}' not found", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(syn.summary())
        print()
        fmt = "{:<30} {:>6}  {:^6}  {:^6}  {:^8}  {}"
        header = fmt.format("KEY", "SCORE", "LOCKED", "PINNED", "EXPIRED", "TAGS")
        print(header)
        print("-" * len(header))
        for s in syn.secrets:
            tags_str = ",".join(s.tags) if s.tags else "-"
            print(
                fmt.format(
                    s.key,
                    s.score,
                    "yes" if s.locked else "no",
                    "yes" if s.pinned else "no",
                    "yes" if s.expired else "no",
                    tags_str,
                )
            )
    else:
        print(syn.summary())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-synopsis",
        description="Display a summary report for a project.",
    )
    sub = parser.add_subparsers(dest="command")

    p_show = sub.add_parser("show", help="Show project synopsis")
    p_show.add_argument("project", help="Project name")
    p_show.add_argument(
        "-v", "--verbose", action="store_true", help="Show per-secret details"
    )
    p_show.set_defaults(func=cmd_synopsis)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
