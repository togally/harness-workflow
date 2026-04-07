from __future__ import annotations

import argparse
from pathlib import Path

from harness_workflow.core import (
    create_change,
    create_plan,
    create_requirement,
    create_version,
    init_repo,
    install_repo,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install harness skill and initialize current repository.")
    install_parser.add_argument("--root", default=".", help="Repository root.")
    install_parser.add_argument("--force-skill", action="store_true", help="Overwrite existing local .codex/skills/harness.")

    init_parser = subparsers.add_parser("init", help="Initialize harness docs structure.")
    init_parser.add_argument("--root", default=".", help="Repository root.")
    init_parser.add_argument("--write-agents", action="store_true", help="Create AGENTS.md if missing.")
    init_parser.add_argument("--write-claude", action="store_true", help="Create CLAUDE.md if missing.")

    req_parser = subparsers.add_parser("requirement", help="Create a requirement workspace.")
    req_parser.add_argument("--root", default=".", help="Repository root.")
    req_parser.add_argument("--id", required=True, help="Requirement id.")
    req_parser.add_argument("--title", required=True, help="Requirement title.")

    change_parser = subparsers.add_parser("change", help="Create a change workspace.")
    change_parser.add_argument("--root", default=".", help="Repository root.")
    change_parser.add_argument("--id", required=True, help="Change id.")
    change_parser.add_argument("--title", required=True, help="Change title.")
    change_parser.add_argument("--requirement", default="", help="Requirement id to link.")

    plan_parser = subparsers.add_parser("plan", help="Show the plan file for a change.")
    plan_parser.add_argument("--root", default=".", help="Repository root.")
    plan_parser.add_argument("--change", required=True, help="Change id.")

    version_parser = subparsers.add_parser("version", help="Snapshot current docs into a version.")
    version_parser.add_argument("--root", default=".", help="Repository root.")
    version_parser.add_argument("--id", required=True, help="Version id.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "install":
        return install_repo(root, force_skill=args.force_skill)
    if args.command == "init":
        return init_repo(root, args.write_agents, args.write_claude)
    if args.command == "requirement":
        return create_requirement(root, args.id, args.title)
    if args.command == "change":
        return create_change(root, args.id, args.title, args.requirement)
    if args.command == "plan":
        return create_plan(root, args.change)
    if args.command == "version":
        return create_version(root, args.id)
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
