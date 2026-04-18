from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import questionary

from harness_workflow.core import (
    archive_requirement,
    archive_suggestion,
    create_bugfix,
    create_change,
    create_regression,
    create_requirement,
    create_suggestion,
    delete_suggestion,
    enter_workflow,
    exit_workflow,
    export_feedback,
    init_repo,
    install_repo,
    install_agent,
    scan_project,
    list_active_requirements,
    list_done_requirements,
    list_suggestions,
    rename_change,
    rename_requirement,
    regression_action,
    set_language,
    update_repo,
    validate_requirement,
    workflow_fast_forward,
    workflow_next,
    workflow_status,
    apply_suggestion,
    apply_all_suggestions,
    search_tools,
    rate_tool,
    log_action,
)


def prompt_platform_selection(current_platforms: Optional[list[str]] = None) -> list[str]:
    """
    交互式平台多选

    Args:
        current_platforms: 当前已激活的平台列表（用于预选）

    Returns:
        用户选择的平台列表
    """
    import sys

    # If not in an interactive terminal, return current or default
    if not sys.stdin.isatty():
        if current_platforms:
            return current_platforms
        return ["codex", "qoder", "cc", "kimi"]

    platforms = questionary.checkbox(
        "选择要支持的平台（空格选择，回车确认）:",
        choices=[
            {
                "name": "codex (AGENTS.md)",
                "value": "codex",
                "checked": current_platforms is None or "codex" in (current_platforms or [])
            },
            {
                "name": "qoder (.qoder/skills/harness/SKILL.md)",
                "value": "qoder",
                "checked": current_platforms is None or "qoder" in (current_platforms or [])
            },
            {
                "name": "cc (.claude/commands/)",
                "value": "cc",
                "checked": current_platforms is None or "cc" in (current_platforms or [])
            },
            {
                "name": "kimi (.kimi/skills/harness/SKILL.md)",
                "value": "kimi",
                "checked": current_platforms is None or "kimi" in (current_platforms or []),
            },
        ]
    ).ask()

    return platforms or []


def prompt_agent_selection() -> str | None:
    """
    交互式 agent 单选

    Returns:
        用户选择的 agent 名称，取消时返回 None
    """
    import sys

    # If not in an interactive terminal, return default
    if not sys.stdin.isatty():
        return "kimi"

    agent = questionary.select(
        "选择目标 agent:",
        choices=[
            {"name": "kimi (.kimi/skills/)", "value": "kimi"},
            {"name": "claude (.claude/skills/)", "value": "claude"},
            {"name": "codex (.codex/skills/)", "value": "codex"},
            {"name": "qoder (.qoder/skills/)", "value": "qoder"},
        ],
        default="kimi",
    ).ask()

    return agent


def prompt_requirement_selection(requirements: list[dict], preselect: str | None = None) -> str | None:
    """
    交互式需求单选

    Args:
        requirements: list of {"req_id": str, "title": str, "stage": str}
        preselect: 预选中的 req_id

    Returns:
        选中的 req_id，取消或无需求时返回 None
    """
    import sys

    if not requirements:
        return None

    choices = [
        {
            "name": f"{r['req_id']} {r['title']}（{r['stage']}）" if r.get("title") else r["req_id"],
            "value": r["req_id"],
        }
        for r in requirements
    ]
    default_value = preselect if preselect and any(r["req_id"] == preselect for r in requirements) else requirements[0]["req_id"]

    if not sys.stdin.isatty():
        return default_value

    result = questionary.select(
        "选择需求:",
        choices=choices,
        default=default_value,
    ).ask()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness workflow CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install harness skill and initialize current repository.")
    install_parser.add_argument("--root", default=".", help="Repository root.")
    install_parser.add_argument("--force-skill", action="store_true", help="Overwrite existing local project skills.")
    install_parser.add_argument("--agent", choices=["kimi", "claude", "codex", "qoder"], help="Install harness skill to specific agent directory.")

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
    update_parser.add_argument("--scan", action="store_true", help="Scan project characteristics for skill adaptation.")

    language_parser = subparsers.add_parser("language", help="Switch the repository language profile.")
    language_parser.add_argument("language", help="Language profile: english or cn.")
    language_parser.add_argument("--root", default=".", help="Repository root.")

    enter_parser = subparsers.add_parser("enter", help="Enter harness conversation mode at the current workflow node.")
    enter_parser.add_argument("req_id", nargs="?", default=None, help="Requirement id to enter (optional, shows list if omitted).")
    enter_parser.add_argument("--root", default=".", help="Repository root.")

    exit_parser = subparsers.add_parser("exit", help="Exit harness conversation mode.")
    exit_parser.add_argument("--root", default=".", help="Repository root.")

    status_parser = subparsers.add_parser("status", help="Show the current workflow runtime state.")
    status_parser.add_argument("--root", default=".", help="Repository root.")

    validate_parser = subparsers.add_parser("validate", help="Validate the current requirement's artifacts.")
    validate_parser.add_argument("--root", default=".", help="Repository root.")

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

    bugfix_parser = subparsers.add_parser("bugfix", help="Create a bugfix workspace and enter regression stage.")
    bugfix_parser.add_argument("title", nargs="?", help="Bugfix title.")
    bugfix_parser.add_argument("--root", default=".", help="Repository root.")
    bugfix_parser.add_argument("--id", help="Optional explicit bugfix id.")
    bugfix_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")

    change_parser = subparsers.add_parser("change", help="Create a change inside the active version.")
    change_parser.add_argument("title", nargs="?", help="Change title.")
    change_parser.add_argument("--root", default=".", help="Repository root.")
    change_parser.add_argument("--id", help="Optional explicit change id.")
    change_parser.add_argument("--title", dest="title_flag", help="Legacy title flag.")
    change_parser.add_argument("--requirement", default="", help="Optional requirement title or id to link.")

    archive_parser = subparsers.add_parser("archive", help="Archive one completed requirement.")
    archive_parser.add_argument("requirement", nargs="?", default=None, help="Requirement title or id (optional, shows list if omitted).")
    archive_parser.add_argument("--root", default=".", help="Repository root.")
    archive_parser.add_argument("--folder", default="", help="Optional subfolder name within archive/.")

    rename_parser = subparsers.add_parser("rename", help="Rename a requirement or change.")
    rename_parser.add_argument("kind", choices=["requirement", "change"], help="Artifact kind.")
    rename_parser.add_argument("current", help="Current title or id.")
    rename_parser.add_argument("new", help="New title or id.")
    rename_parser.add_argument("--root", default=".", help="Repository root.")

    suggest_parser = subparsers.add_parser("suggest", help="Create, list, apply, or delete suggestions.")
    suggest_parser.add_argument("content", nargs="?", help="Suggestion content.")
    suggest_parser.add_argument("--root", default=".", help="Repository root.")
    suggest_parser.add_argument("--title", help="Optional title for the suggestion (used in filename).")
    suggest_parser.add_argument("--list", action="store_true", help="List all pending suggestions.")
    suggest_parser.add_argument("--apply", dest="apply_id", help="Apply a suggestion by id and create a requirement.")
    suggest_parser.add_argument("--apply-all", action="store_true", help="将所有 pending suggest 打包为单一需求并创建.")
    suggest_parser.add_argument("--delete", dest="delete_id", help="Delete a suggestion by id.")
    suggest_parser.add_argument("--archive", dest="archive_id", help="Archive an applied suggestion by id.")
    suggest_parser.add_argument("--pack-title", default="", help="Title for the packed requirement when using --apply-all.")

    tool_parser = subparsers.add_parser("tool-search", help="Search local tool index by keywords.")
    tool_parser.add_argument("keywords", nargs="+", help="Keywords to search for.")
    tool_parser.add_argument("--root", default=".", help="Repository root.")

    rate_parser = subparsers.add_parser("tool-rate", help="Rate a tool and update cumulative average.")
    rate_parser.add_argument("tool_id", help="Tool ID to rate.")
    rate_parser.add_argument("rating", type=int, help="Rating from 1 to 5.")
    rate_parser.add_argument("--root", default=".", help="Repository root.")

    regression_parser = subparsers.add_parser("regression", help="Start or advance a regression confirmation flow.")
    regression_parser.add_argument("title", nargs="?", help="Start a regression with this title.")
    regression_parser.add_argument("--root", default=".", help="Repository root.")
    regression_parser.add_argument("--status", action="store_true", help="Show the current regression state.")
    regression_parser.add_argument("--confirm", action="store_true", help="Confirm that the current regression is a real problem.")
    regression_parser.add_argument("--reject", action="store_true", help="Mark the current regression as not a real problem.")
    regression_parser.add_argument("--cancel", action="store_true", help="Cancel the current regression flow.")
    regression_parser.add_argument("--change", dest="change_title", default="", help="Convert the confirmed regression into a new change.")
    regression_parser.add_argument("--requirement", dest="requirement_title", default="", help="Convert the confirmed regression into a new requirement update.")
    regression_parser.add_argument("--testing", action="store_true", help="Roll back to testing stage and log the confirmed regression as a bug in testing/bugs/.")

    feedback_parser = subparsers.add_parser("feedback", help="Export feedback event summary.")
    feedback_parser.add_argument("--root", default=".", help="Repository root.")
    feedback_parser.add_argument("--reset", action="store_true", help="Clear the feedback log after export.")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = Path(args.root).resolve()

    if args.command == "install":
        if args.agent:
            return install_agent(root, args.agent)
        agent = prompt_agent_selection()
        if not agent:
            print("No agent selected.")
            return 1
        return install_agent(root, agent)
    if args.command == "init":
        return init_repo(root, args.write_agents, args.write_claude)
    if args.command == "update":
        if args.scan:
            return scan_project(root)
        return update_repo(root, check=args.check, force_managed=args.force_managed)
    if args.command == "language":
        return set_language(root, args.language)
    if args.command == "enter":
        if args.req_id:
            return enter_workflow(root, req_id=args.req_id)
        active_reqs = list_active_requirements(root)
        if not active_reqs:
            print("No active requirements found.")
            return enter_workflow(root)
        selected = prompt_requirement_selection(active_reqs)
        if not selected:
            print("No requirement selected.")
            return 1
        return enter_workflow(root, req_id=selected)
    if args.command == "exit":
        return exit_workflow(root)
    if args.command == "status":
        return workflow_status(root)
    if args.command == "validate":
        return validate_requirement(root)
    if args.command == "next":
        return workflow_next(root, execute=args.execute)
    if args.command == "ff":
        return workflow_fast_forward(root)
    if args.command == "requirement":
        return create_requirement(root, args.title, requirement_id=args.id, title=args.title_flag)
    if args.command == "bugfix":
        return create_bugfix(root, args.title, bugfix_id=args.id, title=args.title_flag)
    if args.command == "change":
        return create_change(root, args.title, change_id=args.id, title=args.title_flag, requirement_id=args.requirement)
    if args.command == "archive":
        done_reqs = list_done_requirements(root)
        if not done_reqs:
            print("No done requirements available to archive.")
            return 1
        selected = prompt_requirement_selection(done_reqs, preselect=args.requirement)
        if not selected:
            print("No requirement selected.")
            return 1
        return archive_requirement(root, selected, folder=args.folder)
    if args.command == "rename":
        if args.kind == "requirement":
            return rename_requirement(root, args.current, args.new)
        return rename_change(root, args.current, args.new)
    if args.command == "suggest":
        if args.list:
            return list_suggestions(root)
        if args.apply_all:
            return apply_all_suggestions(root, pack_title=args.pack_title)
        if args.apply_id:
            return apply_suggestion(root, args.apply_id)
        if args.delete_id:
            return delete_suggestion(root, args.delete_id)
        if args.archive_id:
            return archive_suggestion(root, args.archive_id)
        return create_suggestion(root, args.content or "", title=args.title)
    if args.command == "tool-search":
        root = Path(args.root)
        match = search_tools(root, args.keywords)
        if match is None:
            print("No matching tool found.")
            return 0
        print(f"Matched: {match['tool_id']}")
        print(f"Catalog: {match['catalog']}")
        print(f"Description: {match['description']}")
        print(f"Score: {match['score']}")
        return 0
    if args.command == "tool-rate":
        return rate_tool(Path(args.root), args.tool_id, args.rating)
    if args.command == "regression":
        if args.title and not any([args.status, args.confirm, args.reject, args.cancel, args.change_title, args.requirement_title, args.testing]):
            return create_regression(root, args.title)
        return regression_action(
            root,
            status_only=args.status,
            confirm=args.confirm,
            reject=args.reject,
            cancel=args.cancel,
            change_title=args.change_title,
            requirement_title=args.requirement_title,
            to_testing=args.testing,
        )
    if args.command == "feedback":
        return export_feedback(root, reset=args.reset)
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
