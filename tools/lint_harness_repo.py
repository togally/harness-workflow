#!/usr/bin/env python3
"""Lint a repository for Harness Workflow entrypoints (v2 architecture)."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = [
    "WORKFLOW.md",
    ".workflow/state/runtime.yaml",
    ".workflow/context/index.md",
    ".workflow/context/roles/role-loading-protocol.md",
    ".workflow/context/roles/base-role.md",
    ".workflow/context/roles/stage-role.md",
    ".workflow/context/roles/directors/technical-director.md",
    ".workflow/context/experience/index.md",
    ".workflow/flow/stages.md",
]

REQUIRED_DIRS = [
    ".workflow/state",
    ".workflow/state/requirements",
    ".workflow/context",
    ".workflow/context/roles",
    ".workflow/context/experience",
    ".workflow/context/experience/roles",
    ".workflow/context/experience/tool",
    ".workflow/context/experience/risk",
    ".workflow/flow",
    ".workflow/flow/requirements",
    ".workflow/tools",
    ".workflow/evaluation",
    ".workflow/constraints",
]

STAGE_ROLES = [
    "requirement-review.md",
    "planning.md",
    "executing.md",
    "testing.md",
    "acceptance.md",
    "regression.md",
    "done.md",
    "tools-manager.md",
]

AGENTS_REFS = [
    "WORKFLOW.md",
    ".workflow/context/index.md",
    ".workflow/state/runtime.yaml",
]

CLAUDE_REFS = [
    "WORKFLOW.md",
    ".workflow/context/index.md",
    ".workflow/state/runtime.yaml",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint repository for Harness Workflow v2 architecture.")
    parser.add_argument("--root", default=".", help="Repository root to lint.")
    parser.add_argument("--strict-agents", action="store_true", help="Require AGENTS.md to exist.")
    parser.add_argument("--strict-claude", action="store_true", help="Require CLAUDE.md to exist.")
    parser.add_argument("--strict-stage-roles", action="store_true", help="Require all stage role files to exist.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    missing = []
    warnings = []

    for relative in REQUIRED_FILES:
        if not (root / relative).exists():
            missing.append(relative)

    for relative in REQUIRED_DIRS:
        if not (root / relative).is_dir():
            missing.append(relative)

    if args.strict_stage_roles:
        for role in STAGE_ROLES:
            role_path = root / ".workflow" / "context" / "roles" / role
            if not role_path.exists():
                missing.append(str(role_path.relative_to(root)))

    agents = root / "AGENTS.md"
    if args.strict_agents and not agents.exists():
        missing.append("AGENTS.md")
    elif agents.exists():
        text = agents.read_text(encoding="utf-8")
        for ref in AGENTS_REFS:
            if ref not in text:
                warnings.append(f"AGENTS.md does not mention {ref}")

    claude = root / "CLAUDE.md"
    if args.strict_claude and not claude.exists():
        missing.append("CLAUDE.md")
    elif claude.exists():
        text = claude.read_text(encoding="utf-8")
        for ref in CLAUDE_REFS:
            if ref not in text:
                warnings.append(f"CLAUDE.md does not mention {ref}")

    readme = root / ".workflow" / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for expected in ["WORKFLOW.md", "context/index.md", "state/runtime.yaml"]:
            if expected not in text:
                warnings.append(f".workflow/README.md does not mention {expected}")

    if missing:
        print("Missing required files or directories:")
        for item in missing:
            print(f"- {item}")
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")

    if not missing and not warnings:
        print("Repository Harness Workflow v2 lint passed.")
    elif not missing:
        print("Repository Harness Workflow v2 lint passed with warnings.")

    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
