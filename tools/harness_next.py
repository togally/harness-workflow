#!/usr/bin/env python3
"""Advance the workflow to the next review stage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import workflow_next


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance the workflow to the next review stage.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--execute", action="store_true", help="Confirm execution when already ready_for_execution.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return workflow_next(root, execute=args.execute)


if __name__ == "__main__":
    raise SystemExit(main())
