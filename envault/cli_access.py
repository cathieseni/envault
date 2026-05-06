"""CLI sub-commands for access-control management."""

from __future__ import annotations

import argparse
import sys

from envault import access


def cmd_grant(args: argparse.Namespace) -> None:
    try:
        access.grant(args.project, args.profile, args.key)
        print(f"Granted '{args.profile}' access to '{args.key}' in '{args.project}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_revoke(args: argparse.Namespace) -> None:
    try:
        access.revoke(args.project, args.profile, args.key)
        print(f"Revoked '{args.profile}' access to '{args.key}' in '{args.project}'.")
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_keys(args: argparse.Namespace) -> None:
    keys = access.list_profile_keys(args.project, args.profile)
    if not keys:
        print(f"No keys accessible by profile '{args.profile}'.")
    else:
        for key in sorted(keys):
            print(key)


def cmd_list_profiles(args: argparse.Namespace) -> None:
    profiles = access.list_profiles(args.project)
    if not profiles:
        print("No profiles defined.")
    else:
        for profile in sorted(profiles):
            keys = access.list_profile_keys(args.project, profile)
            print(f"{profile}: {', '.join(sorted(keys))}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-access",
        description="Manage per-profile access control for project secrets.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_grant = sub.add_parser("grant", help="Grant a profile access to a key.")
    p_grant.add_argument("project")
    p_grant.add_argument("profile")
    p_grant.add_argument("key")
    p_grant.set_defaults(func=cmd_grant)

    p_revoke = sub.add_parser("revoke", help="Revoke a profile's access to a key.")
    p_revoke.add_argument("project")
    p_revoke.add_argument("profile")
    p_revoke.add_argument("key")
    p_revoke.set_defaults(func=cmd_revoke)

    p_keys = sub.add_parser("keys", help="List keys accessible by a profile.")
    p_keys.add_argument("project")
    p_keys.add_argument("profile")
    p_keys.set_defaults(func=cmd_list_keys)

    p_profiles = sub.add_parser("profiles", help="List all profiles for a project.")
    p_profiles.add_argument("project")
    p_profiles.set_defaults(func=cmd_list_profiles)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
