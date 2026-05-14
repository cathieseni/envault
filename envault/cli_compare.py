"""CLI entry point for cross-project secret key comparison."""

import argparse
import sys

from envault.compare import compare_projects, compare_many


def cmd_compare(args: argparse.Namespace) -> int:
    targets = args.target
    try:
        results = compare_many(args.source, targets)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    exit_code = 0
    for result in results:
        print(f"\n--- {result.source}  vs  {result.target} ---")
        if result.only_in_source:
            print(f"  Only in '{result.source}':")
            for k in result.only_in_source:
                print(f"    - {k}")
        if result.only_in_target:
            print(f"  Only in '{result.target}':")
            for k in result.only_in_target:
                print(f"    + {k}")
        if result.in_both:
            print(f"  In both ({len(result.in_both)} key(s)):")
            for k in result.in_both:
                print(f"    = {k}")
        if not result.has_differences():
            print("  Projects have identical key sets.")
        else:
            exit_code = 1

    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-compare",
        description="Compare secret keys across projects.",
    )
    parser.add_argument("source", help="Source project name")
    parser.add_argument("target", nargs="+", help="One or more target project names")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(cmd_compare(args))


if __name__ == "__main__":
    main()
