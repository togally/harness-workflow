#!/usr/bin/env python3
"""Switch the repository language profile."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import set_language


def main() -> int:
    parser = argparse.ArgumentParser(description="Switch the repository language profile.")
    parser.add_argument("language", help="Language profile: english or cn.")
    parser.add_argument("--root", default=".", help="Repository root.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return set_language(root, args.language)


if __name__ == "__main__":
    raise SystemExit(main())
