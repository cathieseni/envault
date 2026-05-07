"""CLI entry point for the lint command."""

from __future__ import annotations

import argparse
import sys

from envault.lint import lint_project


def cmd_lint(args: argparse.Namespace) -> None:
    issues = lint_project(args.project)
    if not issues:
        print(f"[OK] No issues found in project '{args.project}'.")
        return

    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]

    for issue in issues:
        level_tag = "[ERROR]  " if issue["level"] == "error" else "[WARNING]"
        print(f"{level_tag} {issue['key']}: {issue['message']}")

    print()
    print(f"Total: {len(errors)} error(s), {len(warnings)} warning(s).")

    if errors:
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-lint",
        description="Lint secrets in a project for common issues.",
    )
    parser.add_argument("project", help="Project name to lint.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cmd_lint(args)


if __name__ == "__main__":
    main()
