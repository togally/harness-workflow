from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional

import questionary
from questionary.prompts.common import Choice

# CLI now forwards to tool scripts - all logic is in tools/ directory


def _get_tools_dir() -> Path:
    """Get the tools directory from the installed harness_workflow package."""
    import harness_workflow
    return Path(harness_workflow.__file__).parent / "tools"


# req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 3（sug-17）：
# CLI 对 cwd 敏感——从任意子目录跑 `harness status` 也能定位到仓库根。
_MAX_LOCATE_DEPTH = 20


def _auto_locate_repo_root(start: Path) -> Path:
    """从 ``start`` 向上最多 ``_MAX_LOCATE_DEPTH`` 层查找 ``.workflow/`` 目录。

    - 命中 → 返回含 ``.workflow/`` 的目录（即 harness repo root）。
    - 上溯到 mount point / filesystem root 仍未命中 → ``raise SystemExit`` with
      actionable message（建议用户 ``harness install`` 或 ``cd`` 到仓库根）。
    """
    current = start.resolve()
    for _ in range(_MAX_LOCATE_DEPTH):
        if (current / ".workflow").is_dir():
            return current
        if current.parent == current:
            break
        current = current.parent
    raise SystemExit(
        f"[harness] Not a harness repository (no .workflow/ found from {start} upward). "
        f"Run `harness install` first or cd to the repo root."
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
            Choice.build({"name": "kimi (.kimi/skills/)", "value": "kimi"}),
            Choice.build({"name": "claude (.claude/skills/)", "value": "claude"}),
            Choice.build({"name": "codex (.codex/skills/)", "value": "codex"}),
            Choice.build({"name": "qoder (.qoder/skills/)", "value": "qoder"}),
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
    # chg-07（CLI 路由修正：harness install 接 install_repo + 移除 harness update --flag
    # 的 install_repo hack）：install 子命令加 --check / --force-managed / --all-platforms
    # 三 flag，透传给 install_repo（与原 update 子命令同名同 dest，行为对齐）。
    install_parser.add_argument(
        "--check",
        action="store_true",
        help="Show what would change without writing files (dry-run drift preview).",
    )
    install_parser.add_argument(
        "--force-managed",
        action="store_true",
        help="Overwrite managed files even if they were modified locally.",
    )
    install_parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Refresh all agents/platforms (compatibility escape hatch; overrides active_agent).",
    )

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
    # bugfix-3（新）问题 1：单 agent 作用域 + 全平台 escape hatch
    update_parser.add_argument(
        "--agent",
        choices=["claude", "codex", "qoder", "kimi"],
        help="Override active agent for this update only (does not persist).",
    )
    update_parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Refresh all agents/platforms (compatibility escape hatch; overrides active_agent).",
    )

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
    # req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 3：
    # --lint 触发契约 7 全量扫描（sug-25）。
    status_parser.add_argument(
        "--lint",
        action="store_true",
        help="Scan contract-7 violations (bare work-item ids) under artifacts/ + sessions/.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate the current requirement's artifacts.")
    validate_parser.add_argument("--root", default=".", help="Repository root.")
    validate_parser.add_argument(
        "--human-docs",
        action="store_true",
        help="Validate human-facing documents landed under artifacts/{branch}/... (req-28 / chg-05).",
    )
    validate_parser.add_argument(
        "--requirement",
        dest="requirement",
        default=None,
        help="Target requirement id for --human-docs (e.g. req-28). Falls back to current_requirement.",
    )
    validate_parser.add_argument(
        "--bugfix",
        dest="bugfix",
        default=None,
        help="Target bugfix id for --human-docs (e.g. bugfix-3). Mutually exclusive with --requirement.",
    )
    # req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 2：
    # --contract {all,7,regression} 自动化契约 1-7 校验（sug-10 / sug-15 / sug-25）。
    validate_parser.add_argument(
        "--contract",
        dest="contract",
        default=None,
        choices=["all", "7", "regression", "triggers"],
        help="Run contract automation check (sug-10/sug-15/sug-25). Default scans contract-7 across all artifacts.",
    )

    next_parser = subparsers.add_parser("next", help="Advance the workflow to the next review stage.")
    next_parser.add_argument("--root", default=".", help="Repository root.")
    next_parser.add_argument("--execute", action="store_true", help="Confirm execution when already ready_for_execution.")

    ff_parser = subparsers.add_parser("ff", help="Fast-forward workflow stages until execution confirmation.")
    ff_parser.add_argument("--root", default=".", help="Repository root.")
    ff_parser.add_argument(
        "--auto",
        action="store_true",
        help="自主推进模式：把 current_requirement 推进到 acceptance 前一步，期间批量 ack 决策点（req-29 5.1/5.2/5.3）。",
    )
    ff_parser.add_argument(
        "--auto-accept",
        dest="auto_accept",
        choices=["low", "all"],
        default=None,
        help="配合 --auto：low=仅 low 风险自动 ack，all=全部自动 ack，未传=每条决策点都交互。",
    )

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

    archive_parser = subparsers.add_parser("archive", help="Archive one completed requirement or bugfix.")
    archive_parser.add_argument("requirement", nargs="?", default=None, help="Requirement/bugfix title or id (optional, shows list if omitted).")
    archive_parser.add_argument("--root", default=".", help="Repository root.")
    archive_parser.add_argument("--folder", default="", help="Optional subfolder name within archive/.")
    archive_parser.add_argument(
        "--force-done",
        dest="force_done",
        action="store_true",
        help="For bugfixes only: bypass stage=='done' gate and force state to done before archiving. Use to sweep historical active bugfixes.",
    )

    rename_parser = subparsers.add_parser("rename", help="Rename a requirement, change, or bugfix.")
    rename_parser.add_argument("kind", choices=["requirement", "change", "bugfix"], help="Artifact kind.")
    rename_parser.add_argument("current", help="Current title or id.")
    rename_parser.add_argument("new", help="New title or id.")
    rename_parser.add_argument("--root", default=".", help="Repository root.")

    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate legacy artifact directories to the current layout.",
    )
    migrate_parser.add_argument(
        "resource",
        choices=["requirements"],
        help="Migration target resource (currently only 'requirements').",
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the migration plan without moving any directory.",
    )
    migrate_parser.add_argument("--root", default=".", help="Repository root.")

    suggest_parser = subparsers.add_parser("suggest", help="Create, list, apply, or delete suggestions.")
    suggest_parser.add_argument("content", nargs="?", help="Suggestion content.")
    suggest_parser.add_argument("--root", default=".", help="Repository root.")
    suggest_parser.add_argument("--title", help="Title for the suggestion（契约 6 要求必填）。")
    suggest_parser.add_argument(
        "--priority",
        default="medium",
        choices=["high", "medium", "low"],
        help="Priority level (high/medium/low), default medium（契约 6）。",
    )
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


def _run_tool_script(script_name: str, args: list[str], root: Path) -> int:
    """Run a tool script and return its exit code."""
    script = _get_tools_dir() / script_name
    cmd = [sys.executable, str(script)] + args + ["--root", str(root)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    # req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 3（sug-17）：
    # 默认 ``--root="."`` 时触发 auto-locate（从 cwd 上溯找 ``.workflow/``）；
    # 用户显式传 ``--root <path>`` 则跳过 auto-locate。
    # 对 ``install`` / ``init`` 两类 bootstrap 命令仍按显式 root 处理，避免首次安装
    # 在无 .workflow 的目录下因 auto-locate 失败而卡壳。
    raw_root = getattr(args, "root", ".")
    if raw_root == "." and args.command not in ("install", "init"):
        try:
            root = _auto_locate_repo_root(Path.cwd())
        except SystemExit:
            # 降级回退：子命令自己处理不存在 .workflow/ 的情形（如 status 的 stderr 提示）
            root = Path(raw_root).resolve()
    else:
        root = Path(raw_root).resolve()

    if args.command == "install":
        # chg-07：install 子命令的 --check / --force-managed / --all-platforms 透传给
        # tools/harness_install.py（→ install_agent + install_repo）；与 update --flag
        # 硬 fail 配合，让 install 成为同步契约的唯一真入口（reg-02 根因 A 收口）。
        extra_args: list[str] = []
        if getattr(args, "check", False):
            extra_args.append("--check")
        if getattr(args, "force_managed", False):
            extra_args.append("--force-managed")
        if getattr(args, "all_platforms", False):
            extra_args.append("--all-platforms")
        if args.agent:
            return _run_tool_script(
                "harness_install.py", ["--agent", args.agent, *extra_args], root
            )
        agent = prompt_agent_selection()
        if not agent:
            print("No agent selected.")
            return 1
        return _run_tool_script(
            "harness_install.py", ["--agent", agent, *extra_args], root
        )
    if args.command == "init":
        cmd_args = []
        if args.write_agents:
            cmd_args.append("--write-agents")
        if args.write_claude:
            cmd_args.append("--write-claude")
        return _run_tool_script("harness_init.py", cmd_args, root)
    if args.command == "update":
        # chg-07（CLI 路由修正：harness install 接 install_repo + 移除 harness update --flag
        # 的 install_repo hack）：
        # `harness update` 是纯角色触发；`--check / --force-managed / --all-platforms
        # / --agent` 已迁到 `harness install --{flag}`；`--scan` 仍走 scan_project
        # （与 install_repo 无关，保留分支）；裸 update 仍打 req-33 / chg-02 引导 + exit 0。
        if getattr(args, "scan", False):
            from harness_workflow.workflow_helpers import scan_project
            return scan_project(root)
        # chg-07：刷新类 flag 硬 fail + stderr 迁移提示
        flag_to_hint = [
            ("check", "--check"),
            ("force_managed", "--force-managed"),
            ("all_platforms", "--all-platforms"),
            ("agent", "--agent"),
        ]
        for attr, flag_name in flag_to_hint:
            if getattr(args, attr, None):
                print(
                    f"harness update {flag_name} 已迁移到 `harness install {flag_name}`，请改用新入口。",
                    file=sys.stderr,
                )
                return 1
        # 裸 `harness update`（无任何 flag）→ req-33 / chg-02 引导 + exit 0
        print("harness update 已重定义为角色契约触发。")
        print("请在 Claude Code / Codex 会话中说 '生成项目现状报告' 召唤 project-reporter。")
        print("CLI 同步职责已迁到 `harness install`。")
        return 0
    if args.command == "language":
        return _run_tool_script("harness_language.py", [args.language], root)
    if args.command == "enter":
        if args.req_id:
            return _run_tool_script("harness_enter.py", [args.req_id], root)
        # Need to list active requirements for interactive selection
        import yaml
        reqs_dir = root / ".workflow" / "state" / "requirements"
        active_reqs = []
        if reqs_dir.exists():
            for f in reqs_dir.iterdir():
                if f.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                    if data.get("status") == "active":
                        active_reqs.append({
                            "req_id": data.get("id", f.stem),
                            "title": data.get("title", ""),
                            "stage": data.get("stage", ""),
                        })
        if not active_reqs:
            print("No active requirements found.")
            return _run_tool_script("harness_enter.py", [], root)
        selected = prompt_requirement_selection(active_reqs)
        if not selected:
            print("No requirement selected.")
            return 1
        return _run_tool_script("harness_enter.py", [selected], root)
    if args.command == "exit":
        return _run_tool_script("harness_exit.py", [], root)
    if args.command == "status":
        # req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 3：
        # --lint 直接走 in-process helper，避免 subprocess 丢 stdout。
        if getattr(args, "lint", False):
            from harness_workflow.workflow_helpers import workflow_status_lint
            return workflow_status_lint(root)
        return _run_tool_script("harness_status.py", [], root)
    if args.command == "validate":
        if getattr(args, "human_docs", False):
            # req-28 / chg-05：对人文档落盘校验分支
            if args.requirement and args.bugfix:
                print("[harness] validate --human-docs: --requirement 与 --bugfix 互斥")
                return 2
            from harness_workflow.validate_human_docs import run_cli as _run_human_docs_cli
            target = args.requirement or args.bugfix  # None → 回退 current_requirement
            return _run_human_docs_cli(root, target)
        # req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 2：
        # --contract {all,7,regression} 契约自动化校验（sug-10 / sug-15 / sug-25）。
        if getattr(args, "contract", None):
            from harness_workflow.validate_contract import run_contract_cli
            return run_contract_cli(root, contract=args.contract)
        return _run_tool_script("harness_validate.py", [], root)
    if args.command == "next":
        cmd_args = []
        if args.execute:
            cmd_args.append("--execute")
        return _run_tool_script("harness_next.py", cmd_args, root)
    if args.command == "ff":
        auto_flag = getattr(args, "auto", False)
        auto_accept = getattr(args, "auto_accept", None)
        # 5.3 约束：`--auto-accept` 必须依赖 `--auto`。
        if auto_accept and not auto_flag:
            parser.error("--auto-accept requires --auto")
        if auto_flag:
            from harness_workflow.ff_auto import workflow_ff_auto
            return workflow_ff_auto(root, auto_accept=auto_accept)
        return _run_tool_script("harness_ff.py", [], root)
    if args.command == "requirement":
        cmd_args = []
        if args.title:
            cmd_args.append(args.title)
        if args.id:
            cmd_args.extend(["--id", args.id])
        if args.title_flag:
            cmd_args.extend(["--title-flag", args.title_flag])
        return _run_tool_script("harness_requirement.py", cmd_args, root)
    if args.command == "bugfix":
        cmd_args = []
        if args.title:
            cmd_args.append(args.title)
        if args.id:
            cmd_args.extend(["--id", args.id])
        if args.title_flag:
            cmd_args.extend(["--title-flag", args.title_flag])
        return _run_tool_script("harness_bugfix.py", cmd_args, root)
    if args.command == "change":
        cmd_args = []
        if args.title:
            cmd_args.append(args.title)
        if args.id:
            cmd_args.extend(["--id", args.id])
        if args.title_flag:
            cmd_args.extend(["--title-flag", args.title_flag])
        if args.requirement:
            cmd_args.extend(["--requirement", args.requirement])
        return _run_tool_script("harness_change.py", cmd_args, root)
    if args.command == "archive":
        # req-28 / chg-03（AC-14）：同时扫 requirements / bugfixes，允许 --force-done。
        # 若调用方显式传入 `--force-done` + 具体 id，跳过 interactive 候选列表，直接
        # 走 helper（否则 active 非 done 的 bugfix 永远进不了候选，--force-done 失去意义）。
        import yaml
        if args.force_done and args.requirement:
            cmd_args = [args.requirement, "--force-done"]
            if args.folder:
                cmd_args.extend(["--folder", args.folder])
            return _run_tool_script("harness_archive.py", cmd_args, root)

        done_reqs: list[dict] = []
        for sub in ("requirements", "bugfixes"):
            state_dir = root / ".workflow" / "state" / sub
            if not state_dir.exists():
                continue
            for f in state_dir.iterdir():
                if f.suffix in (".yaml", ".yml"):
                    data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
                    if data.get("stage") == "done" and data.get("status") != "archived":
                        done_reqs.append({
                            "req_id": data.get("id", f.stem),
                            "title": data.get("title", ""),
                            "stage": data.get("stage", ""),
                        })
        if not done_reqs:
            print("No done requirements available to archive.")
            return 1
        # bugfix-3 / 缺陷 3：archive 默认目标必须 = runtime.current_requirement，
        # 不得盲取 done_reqs[0]。优先用 args.requirement（用户显式传入），否则读
        # runtime.current_requirement 当 preselect。non-tty 场景下
        # prompt_requirement_selection 会直接返回 preselect。
        preselect_value = args.requirement
        if not preselect_value:
            try:
                runtime_path = root / ".workflow" / "state" / "runtime.yaml"
                if runtime_path.exists():
                    rt_data = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
                    preselect_value = str(rt_data.get("current_requirement", "")).strip() or None
                    # 若 current_requirement 不在 done 列表，仍传 preselect=None
                    # 让用户面对原始候选，避免悄悄选了一个 stage != done 的 id。
                    if preselect_value and not any(
                        r["req_id"] == preselect_value for r in done_reqs
                    ):
                        print(
                            f"[archive] current_requirement {preselect_value!r} 不在 done 列表中，"
                            "默认改为提示用户选择。",
                            file=sys.stderr,
                        )
                        preselect_value = None
            except Exception:
                preselect_value = None
        selected = prompt_requirement_selection(done_reqs, preselect=preselect_value)
        if not selected:
            print("No requirement selected.")
            return 1
        cmd_args = [selected]
        if args.folder:
            cmd_args.extend(["--folder", args.folder])
        if args.force_done:
            cmd_args.append("--force-done")
        return _run_tool_script("harness_archive.py", cmd_args, root)
    if args.command == "rename":
        cmd_args = [args.kind, args.current, args.new]
        return _run_tool_script("harness_rename.py", cmd_args, root)
    if args.command == "migrate":
        cmd_args = [args.resource]
        if args.dry_run:
            cmd_args.append("--dry-run")
        return _run_tool_script("harness_migrate.py", cmd_args, root)
    if args.command == "suggest":
        cmd_args = []
        if args.content:
            cmd_args.append(args.content)
        if args.title:
            cmd_args.extend(["--title", args.title])
        if args.priority and args.priority != "medium":
            cmd_args.extend(["--priority", args.priority])
        if args.list:
            cmd_args.append("--list")
        if args.apply_id:
            cmd_args.extend(["--apply", args.apply_id])
        if args.apply_all:
            cmd_args.append("--apply-all")
        if args.delete_id:
            cmd_args.extend(["--delete", args.delete_id])
        if args.archive_id:
            cmd_args.extend(["--archive", args.archive_id])
        if args.pack_title:
            cmd_args.extend(["--pack-title", args.pack_title])
        return _run_tool_script("harness_suggest.py", cmd_args, root)
    if args.command == "tool-search":
        script = _get_tools_dir() / "harness_tool_search.py"
        result = subprocess.run(
            [sys.executable, str(script)] + args.keywords + ["--root", str(root)],
            capture_output=True,
            text=True,
        )
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    if args.command == "tool-rate":
        script = _get_tools_dir() / "harness_tool_rate.py"
        result = subprocess.run(
            [sys.executable, str(script), args.tool_id, str(args.rating), "--root", str(root)],
            capture_output=True,
            text=True,
        )
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    if args.command == "regression":
        cmd_args = []
        if args.title:
            cmd_args.append(args.title)
        if args.status:
            cmd_args.append("--status")
        if args.confirm:
            cmd_args.append("--confirm")
        if args.reject:
            cmd_args.append("--reject")
        if args.cancel:
            cmd_args.append("--cancel")
        if args.change_title:
            cmd_args.extend(["--change", args.change_title])
        if args.requirement_title:
            cmd_args.extend(["--requirement", args.requirement_title])
        if args.testing:
            cmd_args.append("--testing")
        return _run_tool_script("harness_regression.py", cmd_args, root)
    if args.command == "feedback":
        script = _get_tools_dir() / "harness_export_feedback.py"
        cmd = [sys.executable, str(script), "--root", str(root)]
        if args.reset:
            cmd.append("--reset")
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result.returncode
    raise SystemExit(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
