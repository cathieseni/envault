"""CLI interface for searching secrets across projects."""

import argparse
import sys

from envault.search import search_by_key, search_by_value, search_by_tag


def cmd_search(args: argparse.Namespace) -> None:
    project = getattr(args, "project", None)

    if args.mode == "key":
        results = search_by_key(args.pattern, project)
    elif args.mode == "value":
        results = search_by_value(args.pattern, project)
    elif args.mode == "tag":
        results = search_by_tag(args.pattern, project)
    else:
        print(f"Unknown search mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No matches found.")
        return

    for item in results:
        tag_part = ""
        if "tags" in item and item["tags"]:
            tag_part = f"  [tags: {', '.join(sorted(item['tags']))}]"
        print(f"[{item['project']}] {item['key']} = {item['value']}{tag_part}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envault-search",
        description="Search secrets by key pattern, value pattern, or tag.",
    )
    parser.add_argument(
        "mode",
        choices=["key", "value", "tag"],
        help="Search mode: 'key' (glob on key name), 'value' (glob on value), 'tag' (exact tag match).",
    )
    parser.add_argument(
        "pattern",
        help="Pattern or tag to search for.",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="Limit search to a specific project (default: all projects).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    cmd_search(args)


if __name__ == "__main__":
    main()
