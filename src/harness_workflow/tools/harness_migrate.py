#!/usr/bin/env python3
"""Migrate legacy requirement directories to artifacts/{branch}/requirements."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import migrate_requirements


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Migrate legacy requirement directories to "
            "artifacts/{branch}/requirements."
        )
    )
    parser.add_argument(
        "resource",
        choices=["requirements"],
        help="Migration target resource (currently only 'requirements').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the migration plan without moving any directory (rc=0).",
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.resource == "requirements":
        return migrate_requirements(root, dry_run=args.dry_run)
    raise SystemExit(f"Unsupported migrate resource: {args.resource}")


if __name__ == "__main__":
    raise SystemExit(main())
