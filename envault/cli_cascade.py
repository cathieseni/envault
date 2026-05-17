"""CLI for cascade secret propagation."""

import argparse
import sys

from envault.cascade import cascade_secret
from envault.storage import get_vault_dir


def cmd_cascade(args: argparse.Namespace) -> None:
    vault_dir = get_vault_dir()
    if not vault_dir.exists():
        print("No vault initialised.", file=sys.stderr)
        sys.exit(1)

    targets = args.targets if args.targets else None

    try:
        result = cascade_secret(
            source_project=args.project,
            key=args.key,
            targets=targets,
            overwrite=not args.no_overwrite,
        )
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(result.summary())

    if result.errors:
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-cascade",
        description="Cascade a secret from one project to dependent projects.",
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("run", help="Propagate a secret value to target projects.")
    p.add_argument("project", help="Source project name.")
    p.add_argument("key", help="Secret key to propagate.")
    p.add_argument(
        "--targets",
        nargs="+",
        metavar="PROJECT",
        help="Explicit target projects (default: auto-detect from dependencies).",
    )
    p.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip target projects that already define the key.",
    )
    p.set_defaults(func=cmd_cascade)

    return parser


def main() -> None:  # pragma: no cover
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
