#!/usr/bin/env python3
"""Create, list, apply, or delete suggestions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import (
    create_suggestion,
    list_suggestions,
    apply_suggestion,
    apply_all_suggestions,
    delete_suggestion,
    archive_suggestion,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create, list, apply, or delete suggestions.")
    parser.add_argument("content", nargs="?", help="Suggestion content.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--title", help="Title for the suggestion（契约 6 要求必填）。")
    parser.add_argument(
        "--priority",
        default="medium",
        choices=["high", "medium", "low"],
        help="Priority level (high/medium/low), default medium（契约 6）。",
    )
    parser.add_argument("--list", action="store_true", help="List all pending suggestions.")
    parser.add_argument("--apply", dest="apply_id", help="Apply a suggestion by id and create a requirement.")
    parser.add_argument("--apply-all", action="store_true", help="将所有 pending suggest 打包为单一需求并创建.")
    parser.add_argument("--delete", dest="delete_id", help="Delete a suggestion by id.")
    parser.add_argument("--archive", dest="archive_id", help="Archive an applied suggestion by id.")
    parser.add_argument("--pack-title", default="", help="Title for the packed requirement when using --apply-all.")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    if args.list:
        return list_suggestions(root)
    if args.apply_all:
        return apply_all_suggestions(root, pack_title=args.pack_title)
    if args.apply_id:
        return apply_suggestion(root, args.apply_id)
    if args.delete_id:
        return delete_suggestion(root, args.delete_id)
    if args.archive_id:
        return archive_suggestion(root, args.archive_id)

    return create_suggestion(
        root,
        args.content or "",
        title=args.title,
        priority=args.priority,
    )


if __name__ == "__main__":
    raise SystemExit(main())
