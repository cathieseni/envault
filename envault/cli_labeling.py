"""CLI commands for secret labeling in envault."""

import argparse
import sys

from envault.labeling import set_label, remove_label, get_labels, find_by_label, clear_labels


def cmd_label_set(args: argparse.Namespace) -> None:
    try:
        set_label(args.project, args.key, args.label_key, args.label_value)
        print(f"Label '{args.label_key}={args.label_value}' set on '{args.key}'.")
    except (KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_label_remove(args: argparse.Namespace) -> None:
    try:
        remove_label(args.project, args.key, args.label_key)
        print(f"Label '{args.label_key}' removed from '{args.key}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_label_list(args: argparse.Namespace) -> None:
    labels = get_labels(args.project, args.key)
    if not labels:
        print(f"No labels on '{args.key}'.")
    else:
        for lk, lv in sorted(labels.items()):
            print(f"  {lk}={lv}")


def cmd_label_find(args: argparse.Namespace) -> None:
    label_value = args.label_value if hasattr(args, "label_value") else None
    results = find_by_label(args.project, args.label_key, label_value)
    if not results:
        print("No secrets matched.")
    else:
        for secret_key, labels in sorted(results.items()):
            label_str = ", ".join(f"{k}={v}" for k, v in sorted(labels.items()))
            print(f"  {secret_key}: {label_str}")


def cmd_label_clear(args: argparse.Namespace) -> None:
    clear_labels(args.project, args.key)
    print(f"All labels cleared from '{args.key}'.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-label", description="Manage secret labels")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set a label on a secret")
    p_set.add_argument("project")
    p_set.add_argument("key")
    p_set.add_argument("label_key")
    p_set.add_argument("label_value")
    p_set.set_defaults(func=cmd_label_set)

    p_rm = sub.add_parser("remove", help="Remove a label from a secret")
    p_rm.add_argument("project")
    p_rm.add_argument("key")
    p_rm.add_argument("label_key")
    p_rm.set_defaults(func=cmd_label_remove)

    p_ls = sub.add_parser("list", help="List labels on a secret")
    p_ls.add_argument("project")
    p_ls.add_argument("key")
    p_ls.set_defaults(func=cmd_label_list)

    p_find = sub.add_parser("find", help="Find secrets by label")
    p_find.add_argument("project")
    p_find.add_argument("label_key")
    p_find.add_argument("label_value", nargs="?", default=None)
    p_find.set_defaults(func=cmd_label_find)

    p_clear = sub.add_parser("clear", help="Clear all labels from a secret")
    p_clear.add_argument("project")
    p_clear.add_argument("key")
    p_clear.set_defaults(func=cmd_label_clear)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
