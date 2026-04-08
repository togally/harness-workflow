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
    set_language,
    update_repo,
    use_version,
    workflow_fast_forward,
    workflow_next,
    workflow_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install harness skill and initialize current repository.")
    install_parser.add_argument("--root", default=".", help="Repository root.")
    install_parser.add_argument("--force-skill", action="store_true", help="Overwrite existing local project skills.")

    init_parser = subparsers.add_parser("init", help="Initialize harness docs structure.")
    init_parser.add_argument("--root", default=".", help="Repository root.")
    init_parser.add_argument("--write-agents", action="store_true", help="Create AGENTS.md if missing.")
    init_parser.add_argument("--write-claude", action="store_true", help="Create CLAUDE.md if missing.")

    update_parser = subparsers.add_parser("update", help="Refresh harness-managed files in the current repository.")
    update_parser.add_argument("--root", default=".", help="Repository root.")
    update_parser.add_argument("--check", action="store_true", help="Show what would change without writing files.")
    update_parser.add_argument(
        "--force-managed",
        action="store_true",
        help="Overwrite managed files even if they were modified locally.",
    )

    language_parser = subparsers.add_parser("language", help="Switch the repository language profile.")
    language_parser.add_argument("language", help="Language profile: english or cn.")
    language_parser.add_argument("--root", default=".", help="Repository root.")

    use_parser = subparsers.add_parser("use", help="Switch the current active version.")
    use_parser.add_argument("version", help="Version name.")
    use_parser.add_argument("--root", default=".", help="Repository root.")

    status_parser = subparsers.add_parser("status", help="Show the current workflow runtime state.")
    status_parser.add_argument("--root", default=".", help="Repository root.")

    next_parser = subparsers.add_parser("next", help="Advance the workflow to the next review stage.")
    next_parser.add_argument("--root", default=".", help="Repository root.")
    next_parser.add_argument("--execute", action="store_true", help="Confirm execution when already ready_for_execution.")

    ff_parser = subparsers.add_parser("ff", help="Fast-forward workflow stages until execution confirmation.")
    ff_parser.add_argument("--root", default=".", help="Repository root.")

    req_parser = subparsers.add_parser("requirement", help="Create a requirement inside the active version.")
    req_parser.add_argument("title", nargs="?", help="Requirement title.")
    req_parser.add_argument("--root", default=".", help="Repository root.")
    req_parser.add_argument("--id", help="Optional explicit requirement id.")
    req_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")

    change_parser = subparsers.add_parser("change", help="Create a change inside the active version.")
    change_parser.add_argument("title", nargs="?", help="Change title.")
    change_parser.add_argument("--root", default=".", help="Repository root.")
    change_parser.add_argument("--id", help="Optional explicit change id.")
    change_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")
    change_parser.add_argument("--requirement", default="", help="Optional requirement title or id to link.")

    plan_parser = subparsers.add_parser("plan", help="Show the plan file for a change.")
    plan_parser.add_argument("change", nargs="?", help="Change title or id.")
    plan_parser.add_argument("--root", default=".", help="Repository root.")
    plan_parser.add_argument("--change", dest="change_flag", help="Legacy change id flag.")

    version_parser = subparsers.add_parser("version", help="Create or switch the active version workspace.")
    version_parser.add_argument("name", nargs="?", help="Version name.")
    version_parser.add_argument("--root", default=".", help="Repository root.")
    version_parser.add_argument("--id", dest="id_flag", help="Legacy version id flag.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "install":
        return install_repo(root, force_skill=args.force_skill)
    if args.command == "init":
        return init_repo(root, args.write_agents, args.write_claude)
    if args.command == "update":
        return update_repo(root, check=args.check, force_managed=args.force_managed)
    if args.command == "language":
        return set_language(root, args.language)
    if args.command == "use":
        return use_version(root, args.version)
    if args.command == "status":
        return workflow_status(root)
    if args.command == "next":
        return workflow_next(root, execute=args.execute)
    if args.command == "ff":
        return workflow_fast_forward(root)
    if args.command == "requirement":
        return create_requirement(root, args.title, requirement_id=args.id, title=args.title_flag)
    if args.command == "change":
        return create_change(root, args.title, change_id=args.id, title=args.title_flag, requirement_id=args.requirement)
    if args.command == "plan":
        change_name = args.change or args.change_flag
        if not change_name:
            raise SystemExit("A change title or id is required.")
        return create_plan(root, change_name)
    if args.command == "version":
        version_name = args.name or args.id_flag
        if not version_name:
            raise SystemExit("A version name is required.")
        return create_version(root, version_name)
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
