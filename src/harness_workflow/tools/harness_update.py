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
    # bugfix-3（新）问题 1：新增 --agent X 一次性覆盖 + --all-platforms escape hatch
    parser.add_argument(
        "--agent",
        choices=["claude", "codex", "qoder", "kimi"],
        help="Override active agent for this update only (does not persist).",
    )
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Refresh all agents/platforms (compatibility escape hatch; overrides active_agent).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.scan:
        return scan_project(root)
    return update_repo(
        root,
        check=args.check,
        force_managed=args.force_managed,
        force_all_platforms=args.all_platforms,
        agent_override=args.agent,
    )


if __name__ == "__main__":
    raise SystemExit(main())
