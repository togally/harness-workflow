#!/usr/bin/env python3
"""Fast-forward workflow stages until execution confirmation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import workflow_fast_forward


def main() -> int:
    parser = argparse.ArgumentParser(description="Fast-forward workflow stages until execution confirmation.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return workflow_fast_forward(root)


if __name__ == "__main__":
    raise SystemExit(main())
