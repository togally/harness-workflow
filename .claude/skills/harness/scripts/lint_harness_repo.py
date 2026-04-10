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
    "docs/context/project/仓库概览.md",
    "docs/context/team/开发规范.md",
]

REQUIRED_DIRS = [
    "docs/requirements/active",
    "docs/requirements/archive",
    "docs/changes/active",
    "docs/changes/archive",
    "docs/plans/active",
    "docs/plans/archive",
    "docs/versions",
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
    for relative in REQUIRED_DIRS:
        if not (root / relative).exists():
            missing.append(relative)

    agents = root / "AGENTS.md"
    if args.strict_agents and not agents.exists():
        missing.append("AGENTS.md")
    elif agents.exists():
        text = agents.read_text(encoding="utf-8")
        if "docs/memory/constitution.md" not in text:
            warnings.append("AGENTS.md does not mention docs/memory/constitution.md")
        if "docs/context/experience/index.md" not in text:
            warnings.append("AGENTS.md does not mention docs/context/experience/index.md")
        if "docs/context/rules/agent-workflow.md" not in text:
            warnings.append("AGENTS.md does not mention docs/context/rules/agent-workflow.md")
        if "docs/context/rules/risk-rules.md" not in text:
            warnings.append("AGENTS.md does not mention docs/context/rules/risk-rules.md")
        if "docs/context/project/仓库概览.md" not in text:
            warnings.append("AGENTS.md does not mention docs/context/project/仓库概览.md")
        if "docs/context/team/开发规范.md" not in text:
            warnings.append("AGENTS.md does not mention docs/context/team/开发规范.md")

    claude = root / "CLAUDE.md"
    if args.strict_claude and not claude.exists():
        missing.append("CLAUDE.md")
    elif claude.exists():
        text = claude.read_text(encoding="utf-8")
        if "docs/memory/constitution.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/memory/constitution.md")
        if "docs/context/experience/index.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/context/experience/index.md")
        if "docs/context/rules/agent-workflow.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/context/rules/agent-workflow.md")
        if "docs/context/rules/risk-rules.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/context/rules/risk-rules.md")
        if "docs/context/project/仓库概览.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/context/project/仓库概览.md")
        if "docs/context/team/开发规范.md" not in text:
            warnings.append("CLAUDE.md does not mention docs/context/team/开发规范.md")

    readme = root / "docs" / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        for expected in [
            "memory/constitution.md",
            "context/experience/index.md",
            "context/rules/agent-workflow.md",
            "context/rules/risk-rules.md",
            "context/project/仓库概览.md",
            "context/team/开发规范.md",
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
