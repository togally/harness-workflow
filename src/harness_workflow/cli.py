from __future__ import annotations

import argparse
from pathlib import Path

from harness_workflow.core import (
    archive_requirement,
    create_change,
    create_plan,
    create_regression,
    create_requirement,
    create_version,
    enter_workflow,
    exit_workflow,
    init_repo,
    install_repo,
    rename_change,
    rename_requirement,
    rename_version,
    regression_action,
    set_active_version,
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

    active_parser = subparsers.add_parser("active", help="Explicitly set the current active version.")
    active_parser.add_argument("version", help="Version name.")
    active_parser.add_argument("--root", default=".", help="Repository root.")

    enter_parser = subparsers.add_parser("enter", help="Enter harness conversation mode at the current workflow node.")
    enter_parser.add_argument("--root", default=".", help="Repository root.")

    exit_parser = subparsers.add_parser("exit", help="Exit harness conversation mode.")
    exit_parser.add_argument("--root", default=".", help="Repository root.")

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

    archive_parser = subparsers.add_parser("archive", help="Archive one completed requirement and its linked changes inside a version.")
    archive_parser.add_argument("requirement", help="Requirement title or id.")
    archive_parser.add_argument("--root", default=".", help="Repository root.")
    archive_parser.add_argument("--version", default="", help="Optional explicit version name.")

    rename_parser = subparsers.add_parser("rename", help="Rename a version, requirement, or change.")
    rename_parser.add_argument("kind", choices=["version", "requirement", "change"], help="Artifact kind.")
    rename_parser.add_argument("current", help="Current title or id.")
    rename_parser.add_argument("new", help="New title or id.")
    rename_parser.add_argument("--root", default=".", help="Repository root.")
    rename_parser.add_argument("--version", default="", help="Optional explicit version name for requirement/change renames.")

    regression_parser = subparsers.add_parser("regression", help="Start or advance a regression confirmation flow.")
    regression_parser.add_argument("title", nargs="?", help="Start a regression with this title.")
    regression_parser.add_argument("--root", default=".", help="Repository root.")
    regression_parser.add_argument("--status", action="store_true", help="Show the current regression state.")
    regression_parser.add_argument("--confirm", action="store_true", help="Confirm that the current regression is a real problem.")
    regression_parser.add_argument("--reject", action="store_true", help="Mark the current regression as not a real problem.")
    regression_parser.add_argument("--cancel", action="store_true", help="Cancel the current regression flow.")
    regression_parser.add_argument("--change", dest="change_title", default="", help="Convert the confirmed regression into a new change.")
    regression_parser.add_argument("--requirement", dest="requirement_title", default="", help="Convert the confirmed regression into a new requirement update.")

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
    if args.command == "active":
        return set_active_version(root, args.version)
    if args.command == "enter":
        return enter_workflow(root)
    if args.command == "exit":
        return exit_workflow(root)
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
    if args.command == "archive":
        return archive_requirement(root, args.requirement, version_name=args.version)
    if args.command == "rename":
        if args.kind == "version":
            return rename_version(root, args.current, args.new)
        if args.kind == "requirement":
            return rename_requirement(root, args.current, args.new, version_name=args.version)
        return rename_change(root, args.current, args.new, version_name=args.version)
    if args.command == "regression":
        if args.title and not any([args.status, args.confirm, args.reject, args.cancel, args.change_title, args.requirement_title]):
            return create_regression(root, args.title)
        return regression_action(
            root,
            status_only=args.status,
            confirm=args.confirm,
            reject=args.reject,
            cancel=args.cancel,
            change_title=args.change_title,
            requirement_title=args.requirement_title,
        )
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
