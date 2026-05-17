"""CLI commands for secret fingerprinting."""

import argparse
import sys

from envault.fingerprint import (
    record_fingerprint,
    get_fingerprint,
    verify_fingerprint,
    delete_fingerprint,
    list_fingerprints,
)
from envault.secrets import get_secret


def cmd_fp_record(args: argparse.Namespace) -> None:
    value = get_secret(args.project, args.key)
    fp = record_fingerprint(args.project, args.key, value)
    print(f"Fingerprint recorded for '{args.key}': {fp}")


def cmd_fp_get(args: argparse.Namespace) -> None:
    fp = get_fingerprint(args.project, args.key)
    if fp is None:
        print(f"No fingerprint recorded for '{args.key}'.", file=sys.stderr)
        sys.exit(1)
    print(fp)


def cmd_fp_verify(args: argparse.Namespace) -> None:
    value = get_secret(args.project, args.key)
    ok = verify_fingerprint(args.project, args.key, value)
    if ok:
        print(f"OK — current value of '{args.key}' matches stored fingerprint.")
    else:
        print(f"MISMATCH — '{args.key}' has changed since last fingerprint.", file=sys.stderr)
        sys.exit(1)


def cmd_fp_delete(args: argparse.Namespace) -> None:
    removed = delete_fingerprint(args.project, args.key)
    if removed:
        print(f"Fingerprint for '{args.key}' deleted.")
    else:
        print(f"No fingerprint found for '{args.key}'.", file=sys.stderr)
        sys.exit(1)


def cmd_fp_list(args: argparse.Namespace) -> None:
    fps = list_fingerprints(args.project)
    if not fps:
        print("No fingerprints recorded.")
        return
    for key, fp in sorted(fps.items()):
        print(f"{key}: {fp}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-fingerprint", description="Secret fingerprinting")
    sub = parser.add_subparsers(dest="command", required=True)

    for cmd_name, help_text in [
        ("record", "Record fingerprint of current secret value"),
        ("get", "Show stored fingerprint for a key"),
        ("verify", "Verify current value matches stored fingerprint"),
        ("delete", "Delete stored fingerprint for a key"),
    ]:
        p = sub.add_parser(cmd_name, help=help_text)
        p.add_argument("project")
        p.add_argument("key")

    p_list = sub.add_parser("list", help="List all fingerprints for a project")
    p_list.add_argument("project")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "record": cmd_fp_record,
        "get": cmd_fp_get,
        "verify": cmd_fp_verify,
        "delete": cmd_fp_delete,
        "list": cmd_fp_list,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
