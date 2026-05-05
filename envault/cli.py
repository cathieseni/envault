"""Main CLI entry point for envault, wiring all subcommands together."""

import argparse
import sys

from envault.project import register_project, list_projects, get_project, remove_project
from envault.secrets import set_secret, get_secret, delete_secret, list_secrets
from envault.audit import get_audit_log, clear_audit_log
from envault.cli_rotation import cmd_rotate


def cmd_init(args):
    project = register_project(args.name)
    print(f"Project '{project['name']}' registered (id={project['id']}).")


def cmd_list_projects(args):
    projects = list_projects()
    if not projects:
        print("No projects registered.")
        return
    for p in projects:
        print(f"  [{p['id']}] {p['name']}")


def cmd_remove(args):
    remove_project(args.name)
    print(f"Project '{args.name}' removed.")


def cmd_set(args):
    set_secret(args.project, args.key, args.value)
    print(f"Secret '{args.key}' set for project '{args.project}'.")


def cmd_get(args):
    value = get_secret(args.project, args.key)
    print(value)


def cmd_delete_secret(args):
    delete_secret(args.project, args.key)
    print(f"Secret '{args.key}' deleted from project '{args.project}'.")


def cmd_list_secrets(args):
    keys = list_secrets(args.project)
    if not keys:
        print(f"No secrets for project '{args.project}'.")
        return
    for k in keys:
        print(f"  {k}")


def cmd_audit(args):
    events = get_audit_log(args.project)
    if not events:
        print(f"No audit events for project '{args.project}'.")
        return
    for e in events:
        print(f"  [{e['timestamp']}] {e['action']} key={e.get('key', '-')}")


def cmd_clear_audit(args):
    clear_audit_log(args.project)
    print(f"Audit log cleared for project '{args.project}'.")


def build_parser():
    parser = argparse.ArgumentParser(prog="envault", description="Lightweight .env manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Register a new project")
    p_init.add_argument("name")
    p_init.set_defaults(func=cmd_init)

    p_ls = sub.add_parser("projects", help="List registered projects")
    p_ls.set_defaults(func=cmd_list_projects)

    p_rm = sub.add_parser("remove", help="Remove a project")
    p_rm.add_argument("name")
    p_rm.set_defaults(func=cmd_remove)

    p_set = sub.add_parser("set", help="Set a secret")
    p_set.add_argument("project")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="Get a secret value")
    p_get.add_argument("project")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_get)

    p_del = sub.add_parser("delete", help="Delete a secret")
    p_del.add_argument("project")
    p_del.add_argument("key")
    p_del.set_defaults(func=cmd_delete_secret)

    p_lss = sub.add_parser("secrets", help="List secret keys for a project")
    p_lss.add_argument("project")
    p_lss.set_defaults(func=cmd_list_secrets)

    p_rot = sub.add_parser("rotate", help="Rotate secrets")
    p_rot.add_argument("project")
    p_rot.add_argument("key", nargs="?", default=None)
    p_rot.add_argument("--length", type=int, default=32)
    p_rot.set_defaults(func=cmd_rotate)

    p_audit = sub.add_parser("audit", help="Show audit log for a project")
    p_audit.add_argument("project")
    p_audit.set_defaults(func=cmd_audit)

    p_clr = sub.add_parser("clear-audit", help="Clear audit log for a project")
    p_clr.add_argument("project")
    p_clr.set_defaults(func=cmd_clear_audit)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
