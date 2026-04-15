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


def _check_scaffold_v2_sync(root: Path) -> list[str]:
    """Check if src/harness_workflow/assets/scaffold_v2/ is in sync with .workflow/."""
    errors: list[str] = []
    scaffold_root = root / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    if not scaffold_root.exists():
        return errors

    check_files = [
        ".workflow/flow/stages.md",
        "WORKFLOW.md",
        "CLAUDE.md",
    ]
    for relative in check_files:
        source = root / relative
        target = scaffold_root / relative
        if not source.exists():
            continue
        if not target.exists():
            errors.append(f"missing {target.relative_to(root)}")
            continue
        if source.read_text(encoding="utf-8") != target.read_text(encoding="utf-8"):
            errors.append(f"out of sync: {target.relative_to(root)} vs {relative}")
    return errors


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

    scaffold_errors = _check_scaffold_v2_sync(root)

    if missing:
        print("Missing required files:")
        for item in missing:
            print(f"- {item}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")
    if scaffold_errors:
        print("Scaffold v2 sync errors:")
        for item in scaffold_errors:
            print(f"- {item}")
        print("  Fix: cp -R .workflow src/harness_workflow/assets/scaffold_v2/")
        print("       cp WORKFLOW.md CLAUDE.md src/harness_workflow/assets/scaffold_v2/")

    if not missing and not warnings and not scaffold_errors:
        print("Repository docs workflow lint passed.")
    elif not missing:
        print("Repository docs workflow lint passed with warnings.")

    return 1 if (missing or scaffold_errors) else 0


if __name__ == "__main__":
    raise SystemExit(main())
