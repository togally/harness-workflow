#!/usr/bin/env python3
"""Create a requirement inside the active version."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import create_requirement


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a requirement inside the active version.")
    parser.add_argument("title", nargs="?", help="Requirement title.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--id", help="Optional explicit requirement id.")
    parser.add_argument("--title-flag", dest="title_flag", help="Legacy title flag.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    # Handle both positional and legacy --title flag
    title = args.title or args.title_flag
    return create_requirement(root, title, requirement_id=args.id, title=title)


if __name__ == "__main__":
    raise SystemExit(main())
