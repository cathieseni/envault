"""CLI commands for secret rotation in envault."""

import argparse
import json
import sys

from envault.rotation import rotate_secret, rotate_all_secrets


def cmd_rotate(args: argparse.Namespace) -> None:
    """Rotate one or all secrets for a project."""
    try:
        if args.all:
            results = rotate_all_secrets(
                args.project,
                length=args.length,
            )
            if not results:
                print(f"No secrets found for project '{args.project}'.")
                return
            for r in results:
                print(f"  Rotated '{r['key']}' at {r['rotated_at']}")
            print(f"\nRotated {len(results)} secret(s) for project '{args.project}'.")
        else:
            if not args.key:
                print("Error: provide --key KEY or use --all", file=sys.stderr)
                sys.exit(1)
            result = rotate_secret(
                args.project,
                args.key,
                length=args.length,
            )
            print(f"Rotated '{result['key']}' at {result['rotated_at']}")
            if args.show:
                print(f"  New value: {result['new_value']}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault rotate",
        description="Rotate secrets for an envault project.",
    )
    parser.add_argument("project", help="Project name")
    parser.add_argument("--key", "-k", default=None, help="Secret key to rotate")
    parser.add_argument(
        "--all", "-a", action="store_true", help="Rotate all secrets in the project"
    )
    parser.add_argument(
        "--length",
        "-l",
        type=int,
        default=32,
        help="Length of generated secret (default: 32)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Print the new secret value to stdout (use with caution)",
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd_rotate(args)


if __name__ == "__main__":
    main()
