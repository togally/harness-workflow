#!/usr/bin/env python3
"""Apply a minimal Harness-style docs workflow to a repository."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "assets" / "templates"


def render_template(name: str, repo_name: str) -> str:
    text = (TEMPLATE_ROOT / name).read_text(encoding="utf-8")
    return (
        text.replace("{{REPO_NAME}}", repo_name)
        .replace("{{DATE}}", date.today().isoformat())
    )


def write_if_missing(path: Path, content: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a minimal Harness-style docs workflow in a repository.")
    parser.add_argument("--root", default=".", help="Repository root to initialize.")
    parser.add_argument(
        "--write-agents",
        action="store_true",
        help="Create AGENTS.md if missing. Existing AGENTS.md is never overwritten.",
    )
    parser.add_argument(
        "--write-claude",
        action="store_true",
        help="Create CLAUDE.md if missing. Existing CLAUDE.md is never overwritten.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    repo_name = root.name
    created: list[str] = []
    skipped: list[str] = []

    required_dirs = [
        root / "docs" / "context" / "team",
        root / "docs" / "context" / "project",
        root / "docs" / "context" / "experience",
        root / "docs" / "context" / "rules",
        root / "docs" / "changes" / "active",
        root / "docs" / "changes" / "archive",
        root / "docs" / "plans" / "active",
        root / "docs" / "plans" / "archive",
        root / "docs" / "decisions",
        root / "docs" / "runbooks",
        root / "docs" / "templates",
        root / "docs" / "memory",
        root / "tools",
    ]

    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)

    write_if_missing(root / "docs" / "README.md", render_template("docs-README.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "memory" / "constitution.md", render_template("constitution.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "context" / "experience" / "index.md", render_template("experience-index.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "context" / "rules" / "agent-workflow.md", render_template("agent-workflow.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "context" / "rules" / "risk-rules.md", render_template("risk-rules.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "context" / "project" / "仓库概览.md", render_template("project-overview.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "context" / "team" / "开发规范.md", render_template("development-standards.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "templates" / "change-requirement.md", render_template("change-requirement.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "templates" / "change-design.md", render_template("change-design.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "templates" / "change-plan.md", render_template("change-plan.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "templates" / "change-acceptance.md", render_template("change-acceptance.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "docs" / "templates" / "session-memory.md", render_template("session-memory.md.tmpl", repo_name), created, skipped)
    write_if_missing(root / "tools" / "lint_harness_repo.py", (Path(__file__).resolve().parents[0] / "lint_harness_repo.py").read_text(encoding="utf-8"), created, skipped)

    if args.write_agents:
        write_if_missing(root / "AGENTS.md", render_template("AGENTS.md.tmpl", repo_name), created, skipped)
    if args.write_claude:
        write_if_missing(root / "CLAUDE.md", render_template("CLAUDE.md.tmpl", repo_name), created, skipped)

    if (root / "doc").exists():
        bridge = root / "docs" / "README.md"
        if bridge.exists():
            text = bridge.read_text(encoding="utf-8")
            marker = "## Legacy Content"
            legacy_note = "\n- Legacy repository docs exist under `doc/` and should be bridged here during migration.\n"
            if marker in text and "Legacy repository docs exist under `doc/`" not in text:
                bridge.write_text(text + legacy_note, encoding="utf-8")

    print("Created files:")
    for path in created:
        print(f"- {path}")
    print("")
    print("Skipped existing files:")
    for path in skipped:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
