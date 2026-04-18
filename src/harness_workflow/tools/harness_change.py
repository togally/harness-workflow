#!/usr/bin/env python3
"""Create a change inside the active version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import create_change


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a change inside the active version.")
    parser.add_argument("title", nargs="?", help="Change title.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--id", help="Optional explicit change id.")
    parser.add_argument("--title-flag", dest="title_flag", help="Legacy title flag.")
    parser.add_argument("--requirement", default="", help="Optional requirement title or id to link.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    title = args.title or args.title_flag
    return create_change(root, title, change_id=args.id, title=title, requirement_id=args.requirement)


if __name__ == "__main__":
    raise SystemExit(main())
