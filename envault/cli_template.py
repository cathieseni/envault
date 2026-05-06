"""CLI entry-point for template rendering commands."""

import argparse
import sys

from envault.template import render_template, list_placeholders


def cmd_render(args: argparse.Namespace) -> None:
    try:
        rendered = render_template(
            project_name=args.project,
            template_path=args.template,
            output_path=args.output,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        print(f"Rendered template written to {args.output}")
    else:
        print(rendered, end="")


def cmd_placeholders(args: argparse.Namespace) -> None:
    try:
        keys = list_placeholders(args.template)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not keys:
        print("No placeholders found.")
    else:
        for key in keys:
            print(key)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-template",
        description="Render secret templates for a project.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="Render a template file with project secrets")
    p_render.add_argument("project", help="Project name")
    p_render.add_argument("template", help="Path to the template file")
    p_render.add_argument("-o", "--output", default=None, help="Write output to this file")
    p_render.set_defaults(func=cmd_render)

    p_ph = sub.add_parser("placeholders", help="List all {{KEY}} placeholders in a template")
    p_ph.add_argument("template", help="Path to the template file")
    p_ph.set_defaults(func=cmd_placeholders)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
