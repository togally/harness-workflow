#!/usr/bin/env python3
"""Analyze a repository for Harness-style initialization readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def detect_languages(root: Path) -> list[str]:
    markers = {
        "python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "node": ["package.json"],
        "java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "go": ["go.mod"],
        "rust": ["Cargo.toml"],
    }
    found = []
    for name, files in markers.items():
        if any((root / marker).exists() for marker in files):
            found.append(name)
    return found


def detect_ci(root: Path) -> list[str]:
    ci = []
    if (root / ".github" / "workflows").exists():
        ci.append("github-actions")
    if (root / ".gitlab-ci.yml").exists():
        ci.append("gitlab-ci")
    if (root / "Jenkinsfile").exists():
        ci.append("jenkins")
    return ci


def recommend_actions(root: Path, facts: dict[str, object]) -> list[str]:
    actions = []
    if not facts["has_docs"]:
        actions.append("Create canonical docs/ entrypoint.")
    if facts["has_legacy_doc"]:
        actions.append("Bridge legacy doc/ into docs/ instead of forcing an immediate move.")
    if not facts["has_agents"]:
        actions.append("Create a short AGENTS.md that routes into docs/.")
    else:
        actions.append("Review existing AGENTS.md and merge docs/ routing rules manually if needed.")
    if not facts["has_constitution"]:
        actions.append("Add.workflow/memory/constitution.md as durable memory root.")
    if not facts["has_experience_index"]:
        actions.append("Add.workflow/context/experience/index.md for keyword-based experience loading.")
    if not facts["has_agent_workflow"]:
        actions.append("Add.workflow/context/rules/agent-workflow.md for detailed workflow rules.")
    return actions


def analyze(root: Path) -> dict[str, object]:
    facts = {
        "root": str(root),
        "has_agents": (root / "AGENTS.md").exists(),
        "has_docs": (root / "docs").exists(),
        "has_legacy_doc": (root / "doc").exists(),
        "has_constitution": (root / "docs" / "memory" / "constitution.md").exists(),
        "has_experience_index": (root / "docs" / "context" / "experience" / "index.md").exists(),
        "has_agent_workflow": (root / "docs" / "context" / "rules" / "agent-workflow.md").exists(),
        "languages": detect_languages(root),
        "ci": detect_ci(root),
    }
    facts["recommended_actions"] = recommend_actions(root, facts)
    return facts


def render_text(report: dict[str, object]) -> str:
    lines = [
        f"Repository: {report['root']}",
        "",
        "Detected:",
        f"- AGENTS.md: {'yes' if report['has_agents'] else 'no'}",
        f"- docs/: {'yes' if report['has_docs'] else 'no'}",
        f"- legacy doc/: {'yes' if report['has_legacy_doc'] else 'no'}",
        f"- constitution: {'yes' if report['has_constitution'] else 'no'}",
        f"- experience index: {'yes' if report['has_experience_index'] else 'no'}",
        f"- agent workflow: {'yes' if report['has_agent_workflow'] else 'no'}",
        f"- languages: {', '.join(report['languages']) if report['languages'] else 'none detected'}",
        f"- ci: {', '.join(report['ci']) if report['ci'] else 'none detected'}",
        "",
        "Recommended actions:",
    ]
    for action in report["recommended_actions"]:
        lines.append(f"- {action}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze repository readiness for Harness-style initialization.")
    parser.add_argument("--root", default=".", help="Repository root to analyze.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = analyze(root)
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
