#!/usr/bin/env python3
"""Archive one completed requirement."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import archive_requirement, list_done_requirements


def main() -> int:
    parser = argparse.ArgumentParser(description="Archive one completed requirement.")
    parser.add_argument("requirement", nargs="?", default=None, help="Requirement title or id (optional, shows list if omitted).")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--folder", default="", help="Optional subfolder name within archive/.")
    args = parser.parse_args()

    root = Path(args.root).resolve()

    # If requirement not provided, we can't prompt interactively from a tool script
    # So we require it to be provided
    if not args.requirement:
        # List done requirements for the user
        done_reqs = list_done_requirements(root)
        if not done_reqs:
            print("No done requirements available to archive.")
            return 1
        # Take the first one as default
        selected = done_reqs[0]["req_id"]
    else:
        selected = args.requirement

    return archive_requirement(root, selected, folder=args.folder)


if __name__ == "__main__":
    raise SystemExit(main())
