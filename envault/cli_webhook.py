"""CLI commands for managing webhooks."""

from __future__ import annotations

import argparse
import sys

from envault.webhook import add_webhook, remove_webhook, list_webhooks


def cmd_webhook_add(args: argparse.Namespace) -> None:
    events = args.events.split(",") if args.events else []
    add_webhook(args.project, args.name, args.url, events)
    print(f"Webhook '{args.name}' added to project '{args.project}'.")


def cmd_webhook_remove(args: argparse.Namespace) -> None:
    try:
        remove_webhook(args.project, args.name)
        print(f"Webhook '{args.name}' removed from project '{args.project}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_webhook_list(args: argparse.Namespace) -> None:
    hooks = list_webhooks(args.project)
    if not hooks:
        print(f"No webhooks registered for project '{args.project}'.")
        return
    for name, cfg in hooks.items():
        events_str = ", ".join(cfg.get("events") or ["<all>"])
        print(f"  {name}  {cfg['url']}  [{events_str}]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-webhook", description="Manage webhooks")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Register a webhook")
    p_add.add_argument("project")
    p_add.add_argument("name", help="Unique webhook name")
    p_add.add_argument("url", help="HTTP(S) endpoint to POST to")
    p_add.add_argument("--events", default="", help="Comma-separated event filter (default: all)")
    p_add.set_defaults(func=cmd_webhook_add)

    p_rm = sub.add_parser("remove", help="Remove a webhook")
    p_rm.add_argument("project")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_webhook_remove)

    p_ls = sub.add_parser("list", help="List webhooks")
    p_ls.add_argument("project")
    p_ls.set_defaults(func=cmd_webhook_list)

    return parser


def main() -> None:  # pragma: no cover
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
