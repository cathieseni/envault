"""CLI for managing redaction rules."""

from __future__ import annotations

import argparse
import sys

from envault.redaction import (
    set_redaction_rule,
    remove_redaction_rule,
    get_redaction_rule,
    list_redaction_rules,
    redact,
)


def cmd_redact_set(args: argparse.Namespace) -> None:
    try:
        set_redaction_rule(
            args.project,
            args.key,
            mask=args.mask,
            pattern=args.pattern or None,
        )
        print(f"Redaction rule set for '{args.key}' in project '{args.project}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_redact_remove(args: argparse.Namespace) -> None:
    try:
        remove_redaction_rule(args.project, args.key)
        print(f"Redaction rule removed for '{args.key}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_redact_list(args: argparse.Namespace) -> None:
    rules = list_redaction_rules(args.project)
    if not rules:
        print(f"No redaction rules for project '{args.project}'.")
        return
    for key, rule in sorted(rules.items()):
        pattern_info = f", pattern={rule['pattern']}" if rule.get("pattern") else ""
        print(f"  {key}: mask={rule['mask']}{pattern_info}")


def cmd_redact_preview(args: argparse.Namespace) -> None:
    from envault.secrets import get_secret

    try:
        value = get_secret(args.project, args.key)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    masked = redact(args.project, args.key, value)
    print(masked)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-redact", description="Manage redaction rules")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set a redaction rule for a key")
    p_set.add_argument("project")
    p_set.add_argument("key")
    p_set.add_argument("--mask", default="***", help="Replacement mask string")
    p_set.add_argument("--pattern", default="", help="Regex pattern to match (optional)")
    p_set.set_defaults(func=cmd_redact_set)

    p_rm = sub.add_parser("remove", help="Remove a redaction rule")
    p_rm.add_argument("project")
    p_rm.add_argument("key")
    p_rm.set_defaults(func=cmd_redact_remove)

    p_ls = sub.add_parser("list", help="List all redaction rules for a project")
    p_ls.add_argument("project")
    p_ls.set_defaults(func=cmd_redact_list)

    p_prev = sub.add_parser("preview", help="Show the redacted value of a key")
    p_prev.add_argument("project")
    p_prev.add_argument("key")
    p_prev.set_defaults(func=cmd_redact_preview)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
