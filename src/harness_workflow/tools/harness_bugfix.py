#!/usr/bin/env python3
"""Create a bugfix workspace and enter regression stage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import create_bugfix


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a bugfix workspace and enter regression stage.")
    parser.add_argument("title", nargs="?", help="Bugfix title.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--id", help="Optional explicit bugfix id.")
    parser.add_argument("--title-flag", dest="title_flag", help="Legacy title flag.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    title = args.title or args.title_flag
    return create_bugfix(root, title, bugfix_id=args.id, title=title)


if __name__ == "__main__":
    raise SystemExit(main())
