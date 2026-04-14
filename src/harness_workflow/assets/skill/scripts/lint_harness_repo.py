#!/usr/bin/env python3
"""Lint a repository for minimal Harness-style workflow entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = [
    "WORKFLOW.md",
    ".workflow/context/index.md",
    ".workflow/state/runtime.yaml",
]

REQUIRED_FILES_LOCALIZED = {
    "english": [
        ".workflow/context/project/project-overview.md",
        ".workflow/context/team/development-standards.md",
    ],
    "cn": [
        ".workflow/context/project/project-overview.md",
        ".workflow/context/team/development-standards.md",
    ],
}

REQUIRED_DIRS = [
    ".workflow/state",
    ".workflow/state/requirements",
    ".workflow/flow",
    ".workflow/flow/requirements",
    ".workflow/context",
    ".workflow/context/roles",
    ".workflow/context/experience",
    ".workflow/constraints",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint repository docs workflow entrypoints.")
    parser.add_argument("--root", default=".", help="Repository root to lint.")
    parser.add_argument("--strict-agents", action="store_true", help="Require AGENTS.md to exist.")
    parser.add_argument("--strict-claude", action="store_true", help="Require CLAUDE.md to exist.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    missing = []
    warnings = []

    for relative in REQUIRED_FILES:
        if not (root / relative).exists():
            missing.append(relative)
    for localized_files in REQUIRED_FILES_LOCALIZED.values():
        for relative in localized_files:
            if not (root / relative).exists():
                missing.append(relative)
                break
    for relative in REQUIRED_DIRS:
        if not (root / relative).exists():
            missing.append(relative)

    if args.strict_agents and not (root / "AGENTS.md").exists():
        missing.append("AGENTS.md")

    if args.strict_claude and not (root / "CLAUDE.md").exists():
        missing.append("CLAUDE.md")

    if missing:
        print("Missing required files:")
        for item in missing:
            print(f"- {item}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")

    if not missing and not warnings:
        print("Repository docs workflow lint passed.")
    elif not missing:
        print("Repository docs workflow lint passed with warnings.")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
