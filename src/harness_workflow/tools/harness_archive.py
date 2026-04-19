#!/usr/bin/env python3
"""Archive one completed requirement or bugfix."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import archive_requirement, list_done_requirements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Archive one completed requirement or bugfix."
    )
    parser.add_argument(
        "requirement",
        nargs="?",
        default=None,
        help="Requirement/bugfix title or id (optional, shows list if omitted).",
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--folder",
        default="",
        help="Optional subfolder name within archive/.",
    )
    parser.add_argument(
        "--force-done",
        dest="force_done",
        action="store_true",
        help=(
            "For bugfixes only: bypass the stage=='done' gate, force the bugfix "
            "state yaml to done/archived before moving. Use when sweeping historical "
            "active bugfixes. The operator is responsible for correctness."
        ),
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()

    # If requirement not provided, pick the first done req/bugfix
    if not args.requirement:
        done_reqs = list_done_requirements(root)
        if not done_reqs:
            print("No done requirements available to archive.")
            return 1
        selected = done_reqs[0]["req_id"]
    else:
        selected = args.requirement

    return archive_requirement(
        root,
        selected,
        folder=args.folder,
        force_done=args.force_done,
    )


if __name__ == "__main__":
    raise SystemExit(main())
