#!/usr/bin/env python3
"""Rename a requirement or change."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import rename_requirement, rename_change


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename a requirement or change.")
    parser.add_argument("kind", choices=["requirement", "change"], help="Artifact kind.")
    parser.add_argument("current", help="Current title or id.")
    parser.add_argument("new", help="New title or id.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.kind == "requirement":
        return rename_requirement(root, args.current, args.new)
    return rename_change(root, args.current, args.new)


if __name__ == "__main__":
    raise SystemExit(main())
