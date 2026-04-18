#!/usr/bin/env python3
"""Initialize harness docs structure."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import init_repo


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize harness docs structure.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--write-agents", action="store_true", help="Create AGENTS.md if missing.")
    parser.add_argument("--write-claude", action="store_true", help="Create CLAUDE.md if missing.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    return init_repo(root, args.write_agents, args.write_claude)


if __name__ == "__main__":
    raise SystemExit(main())
