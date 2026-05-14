"""CLI entry-point for namespace sub-commands."""

import argparse
import sys

from envault.namespace import (
    set_in_namespace,
    get_in_namespace,
    list_namespace,
    delete_namespace,
    list_namespaces,
)


def cmd_ns_set(args: argparse.Namespace) -> None:
    fqk = set_in_namespace(args.project, args.namespace, args.key, args.value)
    print(f"Set {fqk}")


def cmd_ns_get(args: argparse.Namespace) -> None:
    try:
        value = get_in_namespace(args.project, args.namespace, args.key)
        print(value)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ns_list(args: argparse.Namespace) -> None:
    secrets = list_namespace(args.project, args.namespace)
    if not secrets:
        print(f"No secrets in namespace '{args.namespace}'.")
        return
    for k, v in sorted(secrets.items()):
        print(f"  {k} = {v}")


def cmd_ns_delete(args: argparse.Namespace) -> None:
    removed = delete_namespace(args.project, args.namespace)
    if removed:
        for fqk in removed:
            print(f"Deleted {fqk}")
    else:
        print(f"No secrets found in namespace '{args.namespace}'.")


def cmd_ns_namespaces(args: argparse.Namespace) -> None:
    ns_list = list_namespaces(args.project)
    if not ns_list:
        print("No namespaces found.")
    else:
        for ns in ns_list:
            print(f"  {ns}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="envault-namespace", description="Manage secret namespaces")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set a secret in a namespace")
    p_set.add_argument("project")
    p_set.add_argument("namespace")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_ns_set)

    p_get = sub.add_parser("get", help="Get a secret from a namespace")
    p_get.add_argument("project")
    p_get.add_argument("namespace")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_ns_get)

    p_list = sub.add_parser("list", help="List secrets in a namespace")
    p_list.add_argument("project")
    p_list.add_argument("namespace")
    p_list.set_defaults(func=cmd_ns_list)

    p_del = sub.add_parser("delete", help="Delete all secrets in a namespace")
    p_del.add_argument("project")
    p_del.add_argument("namespace")
    p_del.set_defaults(func=cmd_ns_delete)

    p_ns = sub.add_parser("namespaces", help="List all namespaces in a project")
    p_ns.add_argument("project")
    p_ns.set_defaults(func=cmd_ns_namespaces)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
