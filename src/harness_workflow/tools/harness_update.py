#!/usr/bin/env python3
"""Refresh harness-managed files in the current repository."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import update_repo, scan_project


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh harness-managed files in the current repository.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--check", action="store_true", help="Show what would change without writing files.")
    parser.add_argument("--force-managed", action="store_true", help="Overwrite managed files even if they were modified locally.")
    parser.add_argument("--scan", action="store_true", help="Scan project characteristics for skill adaptation.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.scan:
        return scan_project(root)
    return update_repo(root, check=args.check, force_managed=args.force_managed)


if __name__ == "__main__":
    raise SystemExit(main())
