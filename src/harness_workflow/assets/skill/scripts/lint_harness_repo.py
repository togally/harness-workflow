#!/usr/bin/env python3
"""Lint a repository for minimal Harness-style workflow entrypoints."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_FILES = [
    "docs/README.md",
    "docs/memory/constitution.md",
    "docs/context/experience/index.md",
    "docs/context/rules/agent-workflow.md",
    "docs/context/rules/risk-rules.md",
]

REQUIRED_FILES_LOCALIZED = {
    "english": [
        "docs/context/project/project-overview.md",
        "docs/context/team/development-standards.md",
    ],
    "cn": [
        "docs/context/project/project-overview.md",
        "docs/context/team/development-standards.md",
    ],
}

REQUIRED_DIRS = [
    "docs/versions",
    "docs/versions/active",
    "docs/context/hooks",
    "docs/context/rules",
    "docs/context/experience",
    "docs/templates",
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

    agent_guide_refs = [
        "docs/memory/constitution.md",
        "docs/context/experience/index.md",
        "docs/context/rules/agent-workflow.md",
        "docs/context/rules/risk-rules.md",
    ]

    agents = root / "AGENTS.md"
    if args.strict_agents and not agents.exists():
        missing.append("AGENTS.md")
    elif agents.exists():
        text = agents.read_text(encoding="utf-8")
        for ref in agent_guide_refs:
            if ref not in text:
                warnings.append(f"AGENTS.md does not mention {ref}")

    claude = root / "CLAUDE.md"
    if args.strict_claude and not claude.exists():
        missing.append("CLAUDE.md")
    elif claude.exists():
        text = claude.read_text(encoding="utf-8")
        for ref in agent_guide_refs:
            if ref not in text:
                warnings.append(f"CLAUDE.md does not mention {ref}")

    readme = root / "docs" / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for expected in [
            "memory/constitution.md",
            "context/experience/index.md",
            "context/rules/agent-workflow.md",
        ]:
            if expected not in text:
                warnings.append(f"docs/README.md does not mention {expected}")

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
