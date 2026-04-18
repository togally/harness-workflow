#!/usr/bin/env python3
"""Validate the current requirement's artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import validate_requirement


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the current requirement's artifacts.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return validate_requirement(root)


if __name__ == "__main__":
    raise SystemExit(main())
