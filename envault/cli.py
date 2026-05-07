"""Main CLI for envault — combines all sub-commands."""

from __future__ import annotations

import argparse
import sys

from envault.project import register_project, list_projects, get_project, remove_project, ProjectNotFoundError
from envault.secrets import set_secret, get_secret, delete_secret, list_secrets, SecretNotFoundError
from envault.audit import get_audit_log, clear_audit_log
from envault.lint import lint_project


def cmd_init(args: argparse.Namespace) -> None:
    register_project(args.project)
    print(f"Project '{args.project}' initialized.")


def cmd_list_projects(args: argparse.Namespace) -> None:
    projects = list_projects()
    if not projects:
        print("No projects registered.")
    else:
        for p in projects:
            print(p)


def cmd_remove(args: argparse.Namespace) -> None:
    remove_project(args.project)
    print(f"Project '{args.project}' removed.")


def cmd_set(args: argparse.Namespace) -> None:
    set_secret(args.project, args.key, args.value)
    print(f"Secret '{args.key}' set in project '{args.project}'.")


def cmd_get(args: argparse.Namespace) -> None:
    value = get_secret(args.project, args.key)
    print(value)


def cmd_delete(args: argparse.Namespace) -> None:
    delete_secret(args.project, args.key)
    print(f"Secret '{args.key}' deleted from project '{args.project}'.")


def cmd_list_secrets(args: argparse.Namespace) -> None:
    keys = list_secrets(args.project)
    if not keys:
        print(f"No secrets in project '{args.project}'.")
    else:
        for k in keys:
            print(k)


def cmd_audit(args: argparse.Namespace) -> None:
    log = get_audit_log(args.project)
    if not log:
        print(f"No audit log entries for project '{args.project}'.")
    else:
        for entry in log:
            print(f"{entry.get('timestamp', '?')}  {entry.get('action', '?')}  {entry.get('key', '')}")


def cmd_audit_clear(args: argparse.Namespace) -> None:
    clear_audit_log(args.project)
    print(f"Audit log cleared for project '{args.project}'.")


def cmd_lint(args: argparse.Namespace) -> None:
    issues = lint_project(args.project)
    if not issues:
        print(f"[OK] No issues found in project '{args.project}'.")
        return
    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]
    for issue in issues:
        tag = "[ERROR]  " if issue["level"] == "error" else "[WARNING]"
        print(f"{tag} {issue['key']}: {issue['message']}")
    print()
    print(f"Total: {len(errors)} error(s), {len(warnings)} warning(s).")
    if errors:
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault", description="Lightweight .env secret manager.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Register a new project.")
    p_init.add_argument("project")
    p_init.set_defaults(func=cmd_init)

    p_ls = sub.add_parser("projects", help="List all projects.")
    p_ls.set_defaults(func=cmd_list_projects)

    p_rm = sub.add_parser("remove", help="Remove a project.")
    p_rm.add_argument("project")
    p_rm.set_defaults(func=cmd_remove)

    p_set = sub.add_parser("set", help="Set a secret.")
    p_set.add_argument("project")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="Get a secret value.")
    p_get.add_argument("project")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_get)

    p_del = sub.add_parser("delete", help="Delete a secret.")
    p_del.add_argument("project")
    p_del.add_argument("key")
    p_del.set_defaults(func=cmd_delete)

    p_list = sub.add_parser("list", help="List secret keys.")
    p_list.add_argument("project")
    p_list.set_defaults(func=cmd_list_secrets)

    p_audit = sub.add_parser("audit", help="Show audit log.")
    p_audit.add_argument("project")
    p_audit.set_defaults(func=cmd_audit)

    p_audit_clear = sub.add_parser("audit-clear", help="Clear audit log.")
    p_audit_clear.add_argument("project")
    p_audit_clear.set_defaults(func=cmd_audit_clear)

    p_lint = sub.add_parser("lint", help="Lint secrets for common issues.")
    p_lint.add_argument("project")
    p_lint.set_defaults(func=cmd_lint)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except ProjectNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)
    except SecretNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
