"""CLI commands for managing notification channels."""

import argparse
import sys

from envault.notification import (
    add_notification,
    remove_notification,
    list_notifications,
    update_events,
    SUPPORTED_CHANNELS,
)


def cmd_notify_add(args: argparse.Namespace) -> None:
    events = args.events.split(",") if args.events else None
    try:
        entry = add_notification(args.project, args.channel, args.target, events)
        print(f"Notification added: channel={entry['channel']} target={entry['target']} events={entry['events']}")
    except (ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_notify_remove(args: argparse.Namespace) -> None:
    try:
        remove_notification(args.project, args.target)
        print(f"Notification removed: {args.target}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_notify_list(args: argparse.Namespace) -> None:
    entries = list_notifications(args.project)
    if not entries:
        print("No notifications registered.")
        return
    for e in entries:
        print(f"  [{e['channel']}] {e['target']}  events={','.join(e['events'])}")


def cmd_notify_update(args: argparse.Namespace) -> None:
    events = args.events.split(",")
    try:
        entry = update_events(args.project, args.target, events)
        print(f"Updated events for {args.target}: {entry['events']}")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-notify", description="Manage notification channels")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Register a notification channel")
    p_add.add_argument("project")
    p_add.add_argument("channel", choices=SUPPORTED_CHANNELS)
    p_add.add_argument("target", help="Email address, Slack webhook URL, or endpoint URL")
    p_add.add_argument("--events", help="Comma-separated event list (default: rotate,expire,delete)")
    p_add.set_defaults(func=cmd_notify_add)

    p_rm = sub.add_parser("remove", help="Remove a notification channel")
    p_rm.add_argument("project")
    p_rm.add_argument("target")
    p_rm.set_defaults(func=cmd_notify_remove)

    p_ls = sub.add_parser("list", help="List notification channels")
    p_ls.add_argument("project")
    p_ls.set_defaults(func=cmd_notify_list)

    p_up = sub.add_parser("update", help="Update events for a notification channel")
    p_up.add_argument("project")
    p_up.add_argument("target")
    p_up.add_argument("events", help="Comma-separated event list")
    p_up.set_defaults(func=cmd_notify_update)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
