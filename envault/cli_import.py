"""CLI entry point for importing .env files into envault projects."""

import argparse
import sys

from envault.import_env import import_from_file
from envault.storage import get_vault_dir


def cmd_import(args: argparse.Namespace) -> None:
    """Handle the import subcommand."""
    try:
        imported, skipped = import_from_file(
            project_name=args.project,
            filepath=args.file,
            overwrite=args.overwrite,
        )
        print(f"Imported {imported} secret(s) into '{args.project}'.")
        if skipped:
            print(
                f"Skipped {skipped} secret(s) (already exist; use --overwrite to replace)."
            )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"Error: project not found — {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-import",
        description="Import secrets from a .env file into an envault project.",
    )
    parser.add_argument("project", help="Target project name")
    parser.add_argument("file", help="Path to the .env file to import")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing secrets with values from the file",
    )
    parser.add_argument(
        "--vault-dir",
        default=None,
        help="Override the vault directory (default: ~/.envault)",
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.vault_dir:
        import envault.storage as _storage
        _storage._VAULT_DIR_OVERRIDE = args.vault_dir
    cmd_import(args)


if __name__ == "__main__":
    main()
