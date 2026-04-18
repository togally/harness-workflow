#!/usr/bin/env python3
"""Install harness skill to target agent directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import install_agent


def main() -> int:
    parser = argparse.ArgumentParser(description="Install harness skill to target agent directory.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--agent", required=True, help="Target agent (kimi, claude, codex, qoder).")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return install_agent(root, args.agent)


if __name__ == "__main__":
    raise SystemExit(main())
