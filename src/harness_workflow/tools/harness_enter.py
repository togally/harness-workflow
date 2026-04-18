#!/usr/bin/env python3
"""Enter harness conversation mode at the current workflow node."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import enter_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Enter harness conversation mode at the current workflow node.")
    parser.add_argument("req_id", nargs="?", default=None, help="Requirement id to enter (optional, shows list if omitted).")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return enter_workflow(root, req_id=args.req_id or "")


if __name__ == "__main__":
    raise SystemExit(main())
