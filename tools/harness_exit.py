#!/usr/bin/env python3
"""Exit harness conversation mode."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import exit_workflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Exit harness conversation mode.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return exit_workflow(root)


if __name__ == "__main__":
    raise SystemExit(main())
