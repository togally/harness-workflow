from __future__ import annotations

import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import Optional

import yaml

# Version hardcoded to avoid import cycle
__version__ = "0.1.0"

# Backup functions - used by install_repo and update_repo
# These are kept as imports since they are used by exported functions
from harness_workflow.backup import (
    get_active_platforms,
    get_backup_path,
    get_platform_file_patterns,
    read_platforms_config,
    sync_platforms_state,
)
from harness_workflow.slug import slugify_preserve_unicode

PACKAGE_ROOT = files("harness_workflow")
PACKAGE_FS_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")
TEMPLATE_ROOT = SKILL_ROOT.joinpath("assets", "templates")
SCAFFOLD_V2_ROOT = PACKAGE_FS_ROOT / "assets" / "scaffold_v2"
HARNESS_DIR = Path(".codex") / "harness"
MANAGED_STATE_PATH = HARNESS_DIR / "managed-files.json"
CONFIG_PATH = HARNESS_DIR / "config.json"
STATE_RUNTIME_PATH = Path(".workflow") / "state" / "runtime.yaml"
TOOL_KEYWORDS_PATH = Path(".workflow") / "tools" / "index" / "keywords.yaml"
TOOL_RATINGS_PATH = Path(".workflow") / "tools" / "ratings.yaml"
TOOL_MISSING_LOG_PATH = Path(".workflow") / "tools" / "index" / "missing-log.yaml"
WORKFLOW_ENTRYPOINT_PATH = Path("WORKFLOW.md")

DEFAULT_LANGUAGE = "english"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE}
LANGUAGE_ALIASES = {
    "english": "english",
    "en": "english",
    "cn": "cn",
    "zh": "cn",
    "chinese": "cn",
}
DEFAULT_STATE_RUNTIME = {
    "operation_type": "requirement",  # requirement | bugfix | suggestion
    "operation_target": "",           # 当前操作目标
    "current_requirement": "",        # 兼容字段：用于 requirement 类型
    "stage": "",
    "conversation_mode": "open",
    "locked_requirement": "",
    "locked_stage": "",
    "current_regression": "",
    "ff_mode": False,
    "ff_stage_history": [],
    "active_requirements": [],
}
LEGACY_CLEANUP_ROOT = Path(".workflow") / "context" / "backup" / "legacy-cleanup"
LEGACY_CLEANUP_TARGETS = [
    Path("flow"),
    Path(".workflow") / "README.md",
    Path(".workflow") / "memory",
    Path(".workflow") / "decisions",
    Path(".workflow") / "runbooks",
    Path(".workflow") / "templates",
    Path(".workflow") / "context" / "hooks",
    Path(".workflow") / "context" / "rules",
    Path(".workflow") / "context" / "mcp-registry.yaml",
    Path(".workflow") / "context" / "experience" / "index.md",
    Path(".workflow") / "context" / "experience" / "business",
    Path(".workflow") / "context" / "experience" / "architecture",
    Path(".workflow") / "context" / "experience" / "debug",
    Path(".workflow") / "context" / "experience" / "tool" / "playwright.md",
    Path(".workflow") / "context" / "experience" / "tool" / "mysql-mcp.md",
    Path(".workflow") / "context" / "experience" / "tool" / "nacos-mcp.md",
    Path(".workflow") / "state" / "constitution.md",
]
OPTIONAL_EMPTY_DIRS = [
    Path(".workflow") / "flow" / "archive",
]
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
    "testing",
    "acceptance",
    "done",
]
BUGFIX_SEQUENCE = [
    "regression",
    "executing",
    "testing",
    "acceptance",
    "done",
]
SUGGESTION_SEQUENCE = [
    "suggestion",
    "apply",
    "done",
]
LANGUAGE_SPECS = {
    "english": {
        "requirements_dir": "requirements",
        "changes_dir": "changes",
        "plans_dir": "plans",
        "regressions_dir": "regressions",
        "archive_dir": "archive",
        "version_memory": "version-memory.md",
    },
    "cn": {
        "requirements_dir": "需求",
        "changes_dir": "变更",
        "plans_dir": "计划",
        "regressions_dir": "回归",
        "archive_dir": "归档",
        "version_memory": "版本记忆.md",
    },
}

FEEDBACK_DIR = Path(".harness")
FEEDBACK_LOG = FEEDBACK_DIR / "feedback.jsonl"


ITEM_META_ORDER = [
    "id",
    "title",
    "status",
    "kind",
    "requirement",
    "linked_change",
    "linked_requirement",
    "needs_user_input",
    "input_template",
    "owner",
    "created_at",
]

COMMAND_DEFINITIONS = [
    {"name": "harness", "cli": "harness", "hint": "[instruction]"},
    {"name": "harness-install", "cli": "harness install", "hint": ""},
    {"name": "harness-init", "cli": "harness init", "hint": ""},
    {"name": "harness-update", "cli": "harness update", "hint": "[--check|--force-managed]"},
    {"name": "harness-language", "cli": "harness language", "hint": "<english|cn>"},
    {"name": "harness-enter", "cli": "harness enter", "hint": ""},
    {"name": "harness-exit", "cli": "harness exit", "hint": ""},
    {"name": "harness-status", "cli": "harness status", "hint": ""},
    {"name": "harness-requirement", "cli": "harness requirement", "hint": "<title>"},
    {"name": "harness-change", "cli": "harness change", "hint": "<title>"},
    {"name": "harness-bugfix", "cli": "harness bugfix", "hint": "<issue>"},
    {"name": "harness-next", "cli": "harness next", "hint": "[--execute]"},
    {"name": "harness-ff", "cli": "harness ff", "hint": ""},
    {"name": "harness-regression", "cli": "harness regression", "hint": "<issue>|--confirm|--change <title>"},
    {"name": "harness-archive", "cli": "harness archive", "hint": "<requirement>"},
    {"name": "harness-rename", "cli": "harness rename", "hint": "<kind> <old> <new>"},
    {"name": "harness-suggest", "cli": "harness suggest", "hint": "<content>|--list|--apply <id>|--delete <id>"},
]


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    normalized = LANGUAGE_ALIASES.get(value.strip().lower())
    if not normalized:
        supported = ", ".join(sorted(LANGUAGE_ALIASES))
        raise SystemExit(f"Unsupported language: {value}. Supported values: {supported}")
    return normalized


def language_spec(language: str) -> dict[str, str]:
    return LANGUAGE_SPECS[normalize_language(language)]


def template_name(name: str, language: str) -> str:
    if normalize_language(language) == "english":
        english_name = name.replace(".tmpl", ".en.tmpl")
        if TEMPLATE_ROOT.joinpath(english_name).is_file():
            return english_name
    return name


def render_template(
    name: str,
    repo_name: str,
    language: str,
    replacements: dict[str, str] | None = None,
) -> str:
    text = TEMPLATE_ROOT.joinpath(template_name(name, language)).read_text(encoding="utf-8")
    mapping = {
        "{{REPO_NAME}}": repo_name,
        "{{DATE}}": date.today().isoformat(),
        "{{LANGUAGE}}": normalize_language(language),
    }
    if replacements:
        mapping.update({f"{{{{{key}}}}}": value for key, value in replacements.items()})
    for key, value in mapping.items():
        text = text.replace(key, value)
    return text


def _parse_simple_yaml_scalar(value: str) -> object:
    text = value.strip()
    if text == "[]":
        return []
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if text.startswith('"') and text.endswith('"'):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text.strip('"')
    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False
    return text


def load_simple_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload: dict[str, object] = {}
    current_collection_key = ""
    collection_indent = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if current_collection_key and indent > collection_indent:
            if stripped.startswith("- "):
                if not isinstance(payload.get(current_collection_key), list):
                    payload[current_collection_key] = []
                payload[current_collection_key].append(_parse_simple_yaml_scalar(stripped[2:].strip()))
                continue
            if ":" in stripped:
                if not isinstance(payload.get(current_collection_key), dict):
                    payload[current_collection_key] = {}
                sub_key, sub_value = stripped.split(":", 1)
                sub_key = sub_key.strip()
                sub_value = sub_value.strip()
                payload[current_collection_key][sub_key] = _parse_simple_yaml_scalar(sub_value)
                continue
        current_collection_key = ""
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            current_collection_key = key
            collection_indent = indent
            payload[key] = []  # tentatively a list
            continue
        payload[key] = _parse_simple_yaml_scalar(value)
    return payload


def _render_yaml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def _render_yaml_value(value: object, indent: int = 0) -> list[str]:
    prefix = "  " * indent
    lines: list[str] = []
    if isinstance(value, dict):
        if not value:
            lines.append("{}")
            return lines
        for k, v in value.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.extend(_render_yaml_value(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{k}: {_render_yaml_scalar(v)}")
        return lines
    if isinstance(value, list):
        if not value:
            lines.append("[]")
            return lines
        for item in value:
            lines.append(f"{prefix}- {item}")
        return lines
    lines.append(_render_yaml_scalar(value))
    return lines


def save_simple_yaml(path: Path, payload: dict[str, object], ordered_keys: list[str] | None = None) -> None:
    keys = ordered_keys or list(payload.keys())
    lines: list[str] = []
    for key in keys:
        if key not in payload:
            continue
        value = payload[key]
        if isinstance(value, dict):
            if not value:
                lines.append(f"{key}: {{}}")
                continue
            lines.append(f"{key}:")
            lines.extend(_render_yaml_value(value, indent=1))
        elif isinstance(value, list):
            if not value:
                lines.append(f"{key}: []")
                continue
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {_render_yaml_scalar(value)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_requirement_runtime(root: Path) -> dict[str, object]:
    payload = dict(DEFAULT_STATE_RUNTIME)
    payload.update(load_simple_yaml(root / STATE_RUNTIME_PATH))
    active_requirements = payload.get("active_requirements", [])
    if not isinstance(active_requirements, list):
        payload["active_requirements"] = []
    # req-28 / chg-02（AC-12）：懒回填 operation_type / operation_target。
    # 若 runtime.yaml 中缺失（被旧版本 save 裁剪、或人工清空），从 current_requirement
    # 的前缀推断。仅在字段为空时触发，不覆盖已存在的显式值。
    current_req = str(payload.get("current_requirement", "")).strip()
    operation_type = str(payload.get("operation_type", "")).strip()
    operation_target = str(payload.get("operation_target", "")).strip()
    if current_req and not operation_type:
        if current_req.startswith("bugfix-"):
            payload["operation_type"] = "bugfix"
        elif current_req.startswith("sug-"):
            payload["operation_type"] = "suggestion"
        else:
            payload["operation_type"] = "requirement"
    if current_req and not operation_target:
        payload["operation_target"] = current_req
    return payload


def save_requirement_runtime(root: Path, runtime: dict[str, object]) -> None:
    payload = dict(DEFAULT_STATE_RUNTIME)
    payload.update(runtime)
    # req-28 / chg-02（AC-12）：ordered_keys 必须包含 operation_type / operation_target
    # 以及 stage_entered_at，否则 save_simple_yaml 会按白名单裁剪字段，导致
    # `create_bugfix` 写入的 operation_type 在第一次 save→load 往返后丢失，
    # 进而触发 `workflow_next` 走错 sequence → `Unknown stage: regression`。
    save_simple_yaml(
        root / STATE_RUNTIME_PATH,
        payload,
        ordered_keys=[
            "operation_type",
            "operation_target",
            "current_requirement",
            "stage",
            "stage_entered_at",
            "conversation_mode",
            "locked_requirement",
            "locked_stage",
            "current_regression",
            "ff_mode",
            "ff_stage_history",
            "active_requirements",
        ],
    )


def _scaffold_v2_file_contents(root: Path, include_agents: bool, include_claude: bool, language: str) -> dict[str, str]:
    managed: dict[str, str] = {}
    if SCAFFOLD_V2_ROOT.exists():
        for path in sorted(SCAFFOLD_V2_ROOT.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(SCAFFOLD_V2_ROOT).as_posix()
            # 排除 requirements 目录（这些是 harness 自身的开发数据，不应同步到用户项目）
            if "/requirements/" in relative or relative.startswith("requirements/"):
                continue
            managed[relative] = path.read_text(encoding="utf-8")
    repo_name = root.name
    if include_agents:
        managed["AGENTS.md"] = render_template("AGENTS.md.tmpl", repo_name, language)
    if include_claude:
        managed["CLAUDE.md"] = render_template("CLAUDE.md.tmpl", repo_name, language)
    return managed


def render_agent_command(command_name: str, cli_command: str, argument_hint: str, language: str) -> str:
    is_cn = normalize_language(language) == "cn"
    description = (
        f"执行 {cli_command}，并按当前 Harness workflow 状态推进工作"
        if is_cn
        else f"Run {cli_command} and continue work inside the current Harness workflow state"
    )
    if command_name == "harness":
        description = (
            "进入 Harness workflow，并根据当前仓库的 workflow 状态决定下一步"
            if is_cn
            else "Enter the Harness workflow and decide the next action from the current repository workflow state"
        )
    lines = [
        "---",
        f"description: {description}",
        f'argument-hint: "{argument_hint}"',
        "---",
        "",
    ]
    if is_cn:
        lines.extend(
            [
                f"本命令对应 `{cli_command}`。",
                "",
                "## Hard Gate",
                "",
                "未读取 `WORKFLOW.md`、`.workflow/context/index.md`、`.workflow/state/runtime.yaml` 前，立即停止，不执行任何动作。",
                "如果这三个文件任一缺失、冲突或无法解析，立即停止，不允许回退旧入口。",
                "",
                "执行前请先：",
                "",
                "1. 读取根目录 `WORKFLOW.md`",
                "2. 读取 `.workflow/context/index.md`",
                "3. 再读取 `.workflow/state/runtime.yaml`",
                "4. 如有需要，再按 `.workflow/context/index.md` 的路由读取对应角色、经验和约束文件",
                "5. 优先遵循根目录 `AGENTS.md`",
                "6. 如果存在 `.kimi/skills/harness/SKILL.md`、`.qoder/skills/harness/SKILL.md` 或 `.claude/skills/harness/SKILL.md`，按主 Harness skill 执行",
                "",
                "执行要求：",
                "",
                f"- 优先围绕 `{cli_command}` 的语义推进当前任务",
                "- 不要绕过 workflow 手工推进 requirement / change / plan / execution",
                "- 在新节点、子模块切换或上下文压力升高时，先做 context maintenance 判断；无关上下文优先 `/clear`，仍需保留但可压缩的上下文优先 `/compact`",
                "- 如果 workflow 状态缺失或冲突，按命令类型处理：",
                "  - install/init/update/language/status 为独立命令，无需 current_requirement",
                "  - 其他命令需要 current_requirement，缺失时停止并提示",
                "- 如果编译失败、启动失败或需要用户提供外部信息，先进入 regression",
                "- 若需要用户补信息，先填写对应 change `regression/required-inputs.md`",
                "",
                "如果用户补充了额外指令，结合该指令和当前 workflow 状态共同决定下一步。",
            ]
        )
        lines.extend(command_specific_guidance(command_name, language))
    else:
        lines.extend(
            [
                f"This command maps to `{cli_command}`.",
                "",
                "## Hard Gate",
                "",
                "Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.",
                "If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.",
                "",
                "Before acting:",
                "",
                "1. Read the root `WORKFLOW.md`",
                "2. Read `.workflow/context/index.md`",
                "3. Then read `.workflow/state/runtime.yaml`",
                "4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`",
                "5. Prefer the root `AGENTS.md`",
                "6. If `.kimi/skills/harness/SKILL.md`, `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill",
                "",
                "Execution rules:",
                "",
                f"- center the task around `{cli_command}`",
                "- do not bypass the workflow with manual requirement / change / plan / execution steps",
                "- if workflow state is missing or inconsistent, handle by command type:",
                "  - install/init/update/language/status are standalone commands; no current_requirement needed",
                "  - other commands require current_requirement; if missing, stop and prompt user",
                "- if compilation fails, startup fails, or human-provided external input is required, enter regression first",
                "- if human input is required, fill the related change `regression/required-inputs.md` before asking for it",
                "",
                "If the user adds more instruction, combine it with the current workflow state to decide the next step.",
            ]
        )
        lines.extend(command_specific_guidance(command_name, language))
    return "\n".join(lines) + "\n"


def render_codex_command_skill(command_name: str, cli_command: str, language: str) -> str:
    is_cn = normalize_language(language) == "cn"
    description = (
        f"当用户想执行 `{cli_command}` 或表达同类意图时使用。先读取 workflow 状态，再路由到主 harness skill。"
        if is_cn
        else f"Use when the user wants `{cli_command}` or equivalent intent. Read workflow state first, then route into the main harness skill."
    )
    title = command_name.replace("-", " ").title()
    body = [
        "---",
        f"name: {command_name}",
        f'description: "{description}"',
        "---",
        "",
        f"# {title}",
        "",
    ]
    if is_cn:
        body.extend(
            [
                f"这是 `{cli_command}` 的薄包装 skill。",
                "",
                "## Hard Gate",
                "",
                "未读取 `WORKFLOW.md`、`.workflow/context/index.md`、`.workflow/state/runtime.yaml` 前，立即停止，不执行任何动作。",
                "如果这三个文件任一缺失、冲突或无法解析，立即停止，不允许回退旧入口。",
                "",
                "执行前：",
                "",
                "1. 先读取根目录 `WORKFLOW.md`",
                "2. 再读取 `.workflow/context/index.md` 和 `.workflow/state/runtime.yaml`",
                "3. 按 `.workflow/context/index.md` 的路由继续读取匹配的角色、经验和约束文件，再读取根目录 `AGENTS.md` 和主 harness skill：`.codex/skills/harness/SKILL.md`",
                "",
                "规则：",
                "",
                f"- 以 `{cli_command}` 作为当前主要动作",
                "- 不要绕过 workflow 自行创建平行流程",
                "- 如果状态缺失或冲突，停止并提示运行 `harness active \"<version>\"`",
                "- 如果当前仓库里没有全局 `harness` CLI，再回退到 `.codex/skills/harness/scripts/harness.py`",
            ]
        )
        body.extend(command_specific_guidance(command_name, language))
    else:
        body.extend(
            [
                f"This is a thin wrapper skill for `{cli_command}`.",
                "",
                "## Hard Gate",
                "",
                "Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.",
                "If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.",
                "",
                "Before acting:",
                "",
                "1. Read the root `WORKFLOW.md`",
                "2. Read `.workflow/context/index.md` and `.workflow/state/runtime.yaml`",
                "3. Load the matching role / experience / constraint files by following `.workflow/context/index.md`, then read the root `AGENTS.md` and the main harness skill at `.codex/skills/harness/SKILL.md`",
                "",
                "Rules:",
                "",
                f"- treat `{cli_command}` as the primary action",
                "- do not improvise a parallel workflow",
                "- when entering a new node, switching submodules, or nearing context limits, run a context-maintenance check first; prefer `/clear` for irrelevant context and `/compact` for still-relevant but compressible context",
                "- if state is missing or inconsistent, stop and tell the user to run `harness active \"<version>\"`",
                "- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`",
            ]
        )
        body.extend(command_specific_guidance(command_name, language))
    return "\n".join(body) + "\n"


def render_kimi_command_skill(command_name: str, cli_command: str, language: str) -> str:
    is_cn = normalize_language(language) == "cn"
    if is_cn:
        description = f"在 Harness 工作流中运行 {cli_command} 命令"
        hard_gate_lines = [
            "## Hard Gate",
            "",
            "在执行前，必须按顺序读取以下三个文件：",
            "1. 读取根目录 `WORKFLOW.md`",
            "2. 读取 `.workflow/context/index.md`",
            "3. 读取 `.workflow/state/runtime.yaml`",
            "4. 按照 `.workflow/context/index.md` 加载额外的角色/经验/约束文件",
            "5. 优先查看根目录 `AGENTS.md`",
            "6. 如果存在 `.kimi/skills/harness/SKILL.md`，按主 Harness skill 执行",
        ]
    else:
        description = f"Run {cli_command} in the Harness workflow"
        hard_gate_lines = [
            "## Hard Gate",
            "",
            "Do not act until these three files have been read in order:",
            "1. Read the root `WORKFLOW.md`",
            "2. Read `.workflow/context/index.md`",
            "3. Read `.workflow/state/runtime.yaml`",
            "4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`",
            "5. Prefer the root `AGENTS.md`",
            "6. If `.kimi/skills/harness/SKILL.md` exists, follow the main Harness skill",
        ]

    frontmatter = f"---\nname: {command_name}\ndescription: \"{description}\"\n---\n\n"
    body: list[str] = []
    body.extend(hard_gate_lines)
    body.append("")
    body.extend(command_specific_guidance(command_name, language))
    return frontmatter + "\n".join(body)


def command_specific_guidance(command_name: str, language: str) -> list[str]:
    is_cn = normalize_language(language) == "cn"
    guidance: dict[str, list[str]] = {}
    if is_cn:
        guidance = {
            "harness-requirement": [
                "",
                "重点动作：",
                "",
                "- 先确认当前是否已有 active version，没有则提醒先 `harness version` 或 `harness active`",
                "- 创建 requirement 后，优先补齐问题背景、目标、范围、验收边界",
                "- 不要急着进入实现，先和用户讨论需求是否准确",
                "- 如果需求确认完成，明确提示下一步通常是拆 `change` 或运行 `harness next`",
            ],
            "harness-change": [
                "",
                "重点动作：",
                "",
                "- 先识别这是挂在某个 requirement 下，还是一个独立小变更",
                "- 创建 change 后，优先补齐变更目标、影响范围、风险点和验收方式",
                "- 提醒用户 change 完成前必须有 `mvn compile`",
                "- 如果 change 已经讨论清楚，明确提示下一步是 `harness plan` 或 `harness next`",
            ],
            "harness-plan": [
                "",
                "重点动作：",
                "",
                "- 先确认当前 focus change 是哪个",
                "- 计划要拆成可执行步骤，每步尽量带验证动作",
                "- 避免只写大段描述，要让 agent 能直接按步骤执行",
                "- 计划评审完成后，明确提示下一步是 `harness next`",
            ],
            "harness-next": [
                "",
                "重点动作：",
                "",
                "- 先解释当前 stage、current_task 和 next_action",
                "- 再根据当前状态推进，不要假设下一步永远固定",
                "- 如果已经到 `ready_for_execution`，不要直接实施，要提示是否执行或使用 `harness next --execute`",
                "- 如果 workflow 状态不完整，停止并要求先修复状态",
            ],
            "harness-regression": [
                "",
                "重点动作：",
                "",
                "- 不要直接返工，先确认是不是真问题",
                "- 优先利用本机已有日志、编译输出、测试堆栈自行分析",
                "- 如果还需要用户补外部信息，先填写 `regression/required-inputs.md`",
                "- 确认真问题后，再转成新的 requirement 或 change",
            ],
        }
    else:
        guidance = {
            "harness-requirement": [
                "",
                "Focus:",
                "",
                "- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`",
                "- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first",
                "- do not jump into implementation; discuss whether the requirement is correct",
                "- once the requirement is approved, point to splitting changes or running `harness next`",
            ],
            "harness-change": [
                "",
                "Focus:",
                "",
                "- decide whether this change belongs to a requirement or stands alone",
                "- after creating the change, fill in intent, impact scope, risk points, and acceptance method first",
                "- remind the user that every completed change must include `mvn compile`",
                "- once the change is clear, point to `harness plan` or `harness next`",
            ],
            "harness-plan": [
                "",
                "Focus:",
                "",
                "- confirm which change is currently in focus",
                "- break the plan into executable steps and pair each step with verification when possible",
                "- avoid vague prose; the plan should be directly executable by an agent",
                "- once the plan is reviewed, point to `harness next`",
            ],
            "harness-next": [
                "",
                "Focus:",
                "",
                "- explain the current stage, current task, and next action first",
                "- then advance according to the actual state instead of assuming a fixed sequence",
                "- if the version is already `ready_for_execution`, do not start implementation automatically; ask for confirmation or use `harness next --execute`",
                "- if workflow state is incomplete, stop and require state repair first",
            ],
            "harness-enter": [
                "",
                "Focus:",
                "",
                "- enter harness conversation mode at the current version and current workflow node",
                "- after entering, keep the discussion inside the current harness stage instead of drifting into unrelated implementation",
                "- if there is no active version, enter harness mode but explain that the next step is to create or activate a version",
            ],
            "harness-exit": [
                "",
                "Focus:",
                "",
                "- leave harness conversation mode cleanly",
                "- once exited, do not keep enforcing the current harness node as the only valid context",
                "- do not mutate requirement, change, plan, or runtime stage beyond clearing the conversation lock",
            ],
            "harness-regression": [
                "",
                "Focus:",
                "",
                "- do not jump straight into rework; confirm whether it is a real problem first",
                "- use locally available logs, compile output, and test failures before asking the human",
                "- if human-provided external input is still needed, fill `regression/required-inputs.md` first",
                "- only after confirmation should the regression become a new requirement update or change",
            ],
        }
    return guidance.get(command_name, [])


def localized_text(value: dict[str, object], language: str) -> object:
    return value["cn" if normalize_language(language) == "cn" else "english"]


HOOK_TIMINGS = [
    {
        "slug": "session-start",
        "title": {"cn": "会话开始 Hooks", "english": "Session Start Hooks"},
        "purpose": {
            "cn": "新会话开始、恢复会话或显式进入 Harness 模式时，先完成运行态路由、自检和经验加载。",
            "english": "When a session starts, resumes, or explicitly enters Harness mode, route state, self-check, and load experience first.",
        },
        "trigger": {
            "cn": ["新会话开始", "恢复中断会话", "显式执行 `harness enter`"],
            "english": ["a new session starts", "a suspended session resumes", "`harness enter` is called explicitly"],
        },
        "items": [
            {
                "path": "10-load-runtime.md",
                "title": {"cn": "加载运行态", "english": "Load Runtime"},
                "body": {
                    "cn": [
                        "先读取 `.workflow/context/rules/workflow-runtime.yaml`。",
                        "根据 `current_version` 读取当前 version 的 `meta.yaml`。",
                        "如果当前没有 active version，也要明确当前处于未路由状态。",
                    ],
                    "english": [
                        "Read `.workflow/context/rules/workflow-runtime.yaml` first.",
                        "Use `current_version` to read the active version `meta.yaml`.",
                        "If no active version exists, state clearly that the session is not yet routed.",
                    ],
                },
            },
            {
                "path": "20-load-experience-and-risk.md",
                "title": {"cn": "加载经验与风险规则", "english": "Load Experience and Risk Rules"},
                "body": {
                    "cn": [
                        "读取 `.workflow/context/experience/index.md`，只按需加载命中经验。",
                        "读取 `.workflow/context/rules/risk-rules.md`，检查高风险关键词。",
                        "不要一次性全量读取 `.workflow/context/experience/`。",
                    ],
                    "english": [
                        "Read `.workflow/context/experience/index.md` and load only matching experience files.",
                        "Read `.workflow/context/rules/risk-rules.md` and scan for high-risk keywords.",
                        "Do not bulk-load the entire `.workflow/context/experience/` tree.",
                    ],
                },
            },
            {
                "path": "30-stop-on-broken-state.md",
                "title": {"cn": "状态异常立即停止", "english": "Stop on Broken State"},
                "body": {
                    "cn": [
                        "如果 `current_version` 缺失、runtime/config 冲突、version `meta.yaml` 缺失，立即停止。",
                        "不要手工模拟流程继续推进。",
                        "优先提示用户运行 `harness active \"<version>\"` 或修复缺失文件。",
                    ],
                    "english": [
                        "Stop immediately if `current_version` is missing, runtime/config disagree, or the version `meta.yaml` is missing.",
                        "Do not manually simulate the workflow.",
                        "Prefer asking the human to run `harness active \"<version>\"` or restore the missing files.",
                    ],
                },
            },
            {
                "path": "15-detect-subagent-mode.md",
                "title": {"cn": "识别 Subagent 模式", "english": "Detect Subagent Mode"},
                "body": {
                    "cn": [
                        "如果你是作为 subagent 被派发来执行特定任务：不要读取 `workflow-runtime.yaml` 或尝试通过工作流状态路由；从给定的文件或 prompt 中读取任务上下文；只执行分配的任务；将结果写入分配的 change/testing/acceptance 目录下的 `session-memory.md`；不要运行 `harness next` 或任何推进阶段的命令；完成任务后退出。",
                        "如果你是主 agent（通过 `harness enter` 或 harness slash 命令进入）：按正常工作流路由进行；由你控制阶段转换和 subagent 派发。",
                    ],
                    "english": [
                        "If you were dispatched as a subagent to execute a specific task: do NOT read `workflow-runtime.yaml` or attempt to route through workflow state; read your task context from the file or prompt you were given; execute only the assigned task; write results to `session-memory.md` in the assigned change/testing/acceptance directory; do not run `harness next` or any stage-advancing command; exit after completing your task.",
                        "If you are the main agent (you entered via `harness enter` or a harness slash command): proceed with normal workflow routing; you control stage transitions and subagent dispatch.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "before-reply",
        "title": {"cn": "回复前 Hooks", "english": "Before Reply Hooks"},
        "purpose": {
            "cn": "每次正式回复用户前，先判断本次回复是否仍在当前 Harness 节点允许范围内。",
            "english": "Before every substantive reply, verify that the next response still stays inside the current Harness node.",
        },
        "trigger": {
            "cn": ["准备正式回复用户前", "准备解释下一步或执行建议前"],
            "english": ["before a substantive reply to the human", "before explaining the next step or recommended action"],
        },
        "items": [
            {
                "path": "10-respect-conversation-lock.md",
                "title": {"cn": "遵守会话锁", "english": "Respect the Conversation Lock"},
                "body": {
                    "cn": [
                        "如果 `conversation_mode = harness`，先检查 `locked_version`、`locked_stage`、`locked_artifact_kind`、`locked_artifact_id`。",
                        "回复不能脱离当前锁定节点。",
                        "如果需要脱离当前节点，必须先建议或执行 `harness exit`。",
                    ],
                    "english": [
                        "When `conversation_mode = harness`, inspect `locked_version`, `locked_stage`, `locked_artifact_kind`, and `locked_artifact_id` first.",
                        "Do not let the reply drift away from the locked node.",
                        "If a different context is required, suggest or run `harness exit` first.",
                    ],
                },
            },
            {
                "path": "requirement-review/10-request-human-review-first.md",
                "title": {"cn": "需求评审先等用户确认", "english": "Requirement Review Waits for Human Confirmation"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `requirement_review`，回复应优先请求用户审核 requirement 文档。",
                        "不要在用户尚未确认需求时主动推进到拆 change、写 plan 或实施。",
                    ],
                    "english": [
                        "When the current stage is `requirement_review`, prioritize asking the human to review the requirement document.",
                        "Do not proactively move into splitting changes, writing plans, or implementation before the human confirms the requirement.",
                    ],
                },
            },
            {
                "path": "changes-review/10-request-change-review-first.md",
                "title": {"cn": "变更评审先等用户确认", "english": "Changes Review Waits for Human Confirmation"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `changes_review`，回复应优先请求用户审核 change 列表与 change 文档。",
                        "不要在用户尚未确认 change 方案时主动开始写 `plan` 或继续推进阶段。",
                    ],
                    "english": [
                        "When the current stage is `changes_review`, prioritize asking the human to review the change list and change documents.",
                        "Do not proactively start writing plans or continue advancing the workflow before the human confirms the change set.",
                    ],
                },
            },
            {
                "path": "plan-review/10-request-plan-review-first.md",
                "title": {"cn": "计划评审先等用户确认", "english": "Plan Review Waits for Human Confirmation"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `plan_review`，回复应优先请求用户审核 plan 文档。",
                        "不要在用户尚未确认 plan 时主动开始实现或推进执行。",
                    ],
                    "english": [
                        "When the current stage is `plan_review`, prioritize asking the human to review the plan documents.",
                        "Do not proactively start implementation or advance into execution before the human confirms the plan.",
                    ],
                },
            },
            {
                "path": "ready-for-execution/10-request-execution-confirmation.md",
                "title": {"cn": "执行前先等明确确认", "english": "Ready for Execution Waits for Explicit Confirmation"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `ready_for_execution`，回复应优先请求用户确认是否开始实施。",
                        "没有显式确认或 `harness next --execute` 时，不要开始实现。",
                    ],
                    "english": [
                        "When the current stage is `ready_for_execution`, prioritize asking the human whether execution should begin.",
                        "Do not start implementation without explicit confirmation or `harness next --execute`.",
                    ],
                },
            },
            {
                "path": "done/10-request-lesson-capture-before-closure.md",
                "title": {"cn": "收尾前先确认经验沉淀", "english": "Done Stage Requests Lesson Capture Before Closure"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `done`，回复应先确认 `session-memory.md` 是否已更新，以及成熟经验是否已检查。",
                        "不要在经验沉淀缺失时直接宣称工作已完整收尾。",
                    ],
                    "english": [
                        "When the current stage is `done`, first confirm that `session-memory.md` has been updated and mature lessons were reviewed.",
                        "Do not declare the work fully closed while lesson capture is still missing.",
                    ],
                },
            },
            {
                "path": "idle/10-offer-only-workflow-actions.md",
                "title": {"cn": "空闲阶段只提供工作流动作", "english": "Idle Stage Offers Workflow Actions Only"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `idle`，回复只能引导创建 requirement / change 工作区，或继续澄清需求与范围。",
                        "即使用户给了实现型 prompt，也不能在回复里承诺实现、分析实现细节或进入编码准备。",
                    ],
                    "english": [
                        "When the current stage is `idle`, replies may only guide requirement / change workspace creation or continue requirement clarification.",
                        "Even if the user provides an implementation-oriented prompt, do not promise implementation, analyze implementation details, or prepare to code in the reply.",
                    ],
                },
            },
            {
                "path": "testing/10-no-advance-before-cases-pass.md",
                "title": {"cn": "测试阶段：所有用例通过前不推进", "english": "Testing Stage: No Advance Before Cases Pass"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `testing`，且仍有测试用例失败，不要建议或执行 `harness next`。",
                        "如果 `testing/bugs/` 中仍有未关闭的 bug，不要建议或执行 `harness next`。",
                        "如果用户要求推进，先检查 `testing/test-cases.md` 和 `testing/bugs/`。",
                        "只有所有用例通过且无未关闭 bug 时，才可在确认用户意图后推进。",
                    ],
                    "english": [
                        "Do not suggest or perform `harness next` if any test cases are still failing.",
                        "Do not suggest or perform `harness next` if any bugs in `testing/bugs/` are still open.",
                        "If the user asks to advance, check `testing/test-cases.md` and `testing/bugs/` first.",
                        "If all cases pass and no open bugs: confirm with the user before advancing.",
                    ],
                },
            },
            {
                "path": "acceptance/10-require-document-basis.md",
                "title": {"cn": "验收阶段：决策必须有文档依据", "english": "Acceptance Stage: Require Document Basis"},
                "body": {
                    "cn": [
                        "所有验收决策必须基于 `acceptance/acceptance-checklist.md` 中已记录的标准。",
                        "不得仅凭主观印象接受或拒绝。",
                        "如果某个检查项不清晰，应对照需求文档进行澄清。",
                        "没有完整的 `acceptance/sign-off.md` 时，不得推进到 `done`。",
                    ],
                    "english": [
                        "All acceptance decisions must be based on documented criteria in `acceptance/acceptance-checklist.md`.",
                        "Do not accept or reject based on subjective impressions alone.",
                        "If a checklist item is unclear, clarify against the requirement document.",
                        "Do not advance to `done` without a completed `acceptance/sign-off.md`.",
                    ],
                },
            },
            {
                "path": "20-block-workflow-drift.md",
                "title": {"cn": "阻止工作流漂移", "english": "Block Workflow Drift"},
                "body": {
                    "cn": [
                        "如果当前阶段只允许讨论或补文档，不要在回复里承诺直接编码。",
                        "不要因为用户给了详细 prompt，就把它当成越过阶段门禁的授权。",
                    ],
                    "english": [
                        "If the current stage allows discussion or document refinement only, do not promise direct coding in the reply.",
                        "A detailed prompt is not permission to bypass the current stage gate.",
                    ],
                },
            },
            {
                "path": "30-check-stage-boundary.md",
                "title": {"cn": "检查阶段边界", "english": "Check Stage Boundaries"},
                "body": {
                    "cn": [
                        "先检查当前动作是否符合当前 stage。",
                        "如果下一步需要推进 stage，先提示使用 `harness next`、`harness regression` 或其他对应命令。",
                    ],
                    "english": [
                        "Confirm that the planned action fits the current stage.",
                        "If the next step requires a stage transition, point to `harness next`, `harness regression`, or the corresponding command first.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "node-entry",
        "title": {"cn": "工作节点 Hooks", "english": "Workflow Node Hooks"},
        "purpose": {
            "cn": "根据当前工作节点加载对应约束，定义该节点允许做什么、不允许做什么。",
            "english": "Load node-specific constraints that define what is allowed and forbidden in the current workflow node.",
        },
        "trigger": {
            "cn": ["进入某个工作节点", "当前 stage 或 mode 发生变化后"],
            "english": ["when entering a workflow node", "after the stage or mode changes"],
        },
        "items": [
            {
                "path": "idle/10-formalize-workspace-first.md",
                "title": {"cn": "空闲阶段先正式建工作区", "english": "Idle Stage Formalizes a Workspace First"},
                "body": {
                    "cn": [
                        "当前处于 `idle`，说明 requirement / change 工作区还未正式建立。",
                        "此时只能创建或确认 requirement / change 工作区，不能直接进入实现或实现分析。",
                    ],
                    "english": [
                        "The `idle` stage means no requirement / change workspace has been formally established yet.",
                        "At this point, only requirement / change workspace creation or confirmation is allowed; do not jump into implementation or implementation analysis.",
                    ],
                },
            },
            {
                "path": "requirement-review/10-discussion-only.md",
                "title": {"cn": "需求节点只讨论", "english": "Requirement Node Is Discussion Only"},
                "body": {
                    "cn": [
                        "当前节点只允许讨论、澄清、更新 requirement 文档。",
                        "实现型 prompt 只能吸收进需求结论，不能直接开始编码。",
                    ],
                    "english": [
                        "This node allows discussion, clarification, and requirement document updates only.",
                        "Implementation-oriented prompts must be absorbed into the requirement, not used to start coding.",
                    ],
                },
            },
            {
                "path": "requirement-review/20-wait-for-human-approval.md",
                "title": {"cn": "需求节点等待用户确认", "english": "Requirement Node Waits for Human Approval"},
                "body": {
                    "cn": [
                        "创建或更新 requirement 后，当前节点必须停在需求讨论与审核。",
                        "只有用户明确确认需求无误后，才允许进入 `change` 拆分或后续阶段。",
                    ],
                    "english": [
                        "After a requirement is created or updated, this node must stay in discussion and review.",
                        "Only after the human explicitly confirms the requirement may the workflow move into change splitting or later stages.",
                    ],
                },
            },
            {
                "path": "changes-review/20-wait-for-human-approval.md",
                "title": {"cn": "变更节点等待用户确认", "english": "Changes Node Waits for Human Approval"},
                "body": {
                    "cn": [
                        "创建或更新 change 后，当前节点必须停在 change 讨论与审核。",
                        "只有用户明确确认 change 拆分无误后，才允许进入 `plan` 阶段。",
                    ],
                    "english": [
                        "After changes are created or updated, this node must stay in change discussion and review.",
                        "Only after the human explicitly confirms the change split may the workflow move into the `plan` stage.",
                    ],
                },
            },
            {
                "path": "changes-review/10-change-doc-first.md",
                "title": {"cn": "变更节点先补文档", "english": "Change Node Is Document First"},
                "body": {
                    "cn": [
                        "当前节点先补齐 change 文档、影响范围、风险和验收方式。",
                        "没有进入 plan 或 executing 前，不要开始实现。",
                    ],
                    "english": [
                        "At this node, fill the change document, impact scope, risks, and acceptance method first.",
                        "Do not start implementation before plan or executing stage.",
                    ],
                },
            },
            {
                "path": "plan-review/10-plan-before-code.md",
                "title": {"cn": "计划节点先有计划", "english": "Plan Node Requires a Plan"},
                "body": {
                    "cn": [
                        "当前节点必须先形成可执行 plan。",
                        "没有 plan 的情况下，不允许宣称进入实施。",
                    ],
                    "english": [
                        "At this node, an executable plan must exist first.",
                        "Do not claim implementation is ready without a plan.",
                    ],
                },
            },
            {
                "path": "plan-review/20-wait-for-human-approval.md",
                "title": {"cn": "计划节点等待用户确认", "english": "Plan Node Waits for Human Approval"},
                "body": {
                    "cn": [
                        "创建或更新 plan 后，当前节点必须停在计划讨论与审核。",
                        "只有用户明确确认 plan 无误后，才允许进入 `ready_for_execution`。",
                    ],
                    "english": [
                        "After a plan is created or updated, this node must stay in plan discussion and review.",
                        "Only after the human explicitly confirms the plan may the workflow move into `ready_for_execution`.",
                    ],
                },
            },
            {
                "path": "ready-for-execution/10-wait-for-explicit-confirmation.md",
                "title": {"cn": "执行前等待明确确认", "english": "Wait for Explicit Confirmation Before Execution"},
                "body": {
                    "cn": [
                        "当前节点只允许确认执行条件、说明验证门禁，并等待用户确认。",
                        "没有显式执行确认前，不允许进入 `executing`。",
                    ],
                    "english": [
                        "This node may only confirm execution conditions, explain verification gates, and wait for human confirmation.",
                        "Do not enter `executing` before explicit execution approval.",
                    ],
                },
            },
            {
                "path": "done/10-verify-lessons-before-closeout.md",
                "title": {"cn": "收尾节点先确认经验闭环", "english": "Done Node Verifies Lessons Before Closeout"},
                "body": {
                    "cn": [
                        "当前节点先做最终验证、更新 `session-memory.md`，并检查是否有成熟经验需要融入经验库。",
                        "只有验证和经验闭环都完成后，才允许把工作视为完整结束。",
                    ],
                    "english": [
                        "At this node, perform final verification, update `session-memory.md`, and check whether mature lessons belong in the experience library.",
                        "Treat the work as fully complete only after both verification and lesson capture are finished.",
                    ],
                },
            },
            {
                "path": "executing/10-execution-only.md",
                "title": {"cn": "实施节点才允许编码", "english": "Only Executing Node May Code"},
                "body": {
                    "cn": [
                        "只有 `executing` 节点允许开始生产代码实施。",
                        "编码时必须持续遵循 plan 与验证步骤。",
                    ],
                    "english": [
                        "Only the `executing` node may start production implementation work.",
                        "While coding, continue following the plan and its verification steps.",
                    ],
                },
            },
            {
                "path": "regression/10-diagnosis-before-fix.md",
                "title": {"cn": "回归节点先诊断再修复", "english": "Regression Diagnoses Before Fixing"},
                "body": {
                    "cn": [
                        "先确认是不是真问题，再决定是否转成 requirement 或 change。",
                        "不要直接返工。",
                    ],
                    "english": [
                        "Confirm whether it is a real problem before converting it into a requirement or change.",
                        "Do not jump straight into rework.",
                    ],
                },
            },
            {
                "path": "testing/10-spawn-testing-subagent.md",
                "title": {"cn": "测试阶段：派发测试 Subagent", "english": "Testing Stage Entry"},
                "body": {
                    "cn": [
                        "进入 `testing` 阶段时：读取 `testing/test-plan.md`，若不存在则先从模板创建；读取 `testing/test-cases.md`，若不存在则先从模板创建。",
                        "派发 subagent 执行测试计划：subagent 读取测试计划和用例，更新 `testing/test-cases.md` 中的状态列，并将摘要写入 `testing/session-memory.md`。",
                        "subagent 完成后，检查 `testing/test-cases.md` 中的失败项；如有失败，确保每个失败在 `testing/bugs/` 中有对应的 bug 文件。",
                        "所有测试用例通过且无未关闭 bug 前，不得推进到 `acceptance`。",
                    ],
                    "english": [
                        "On entering the `testing` stage: read `testing/test-plan.md` — if it does not exist, create it from the template before proceeding; read `testing/test-cases.md` — if it does not exist, create it from the template.",
                        "Dispatch a subagent to execute the test plan: subagent reads the plan and cases, updates the status column in `testing/test-cases.md`, and writes a summary to `testing/session-memory.md`.",
                        "After subagent completes, review `testing/test-cases.md` for failures; if failures exist, ensure each failure has a corresponding bug file in `testing/bugs/`.",
                        "Do not advance to `acceptance` until all test cases pass and no bugs are open.",
                    ],
                },
            },
            {
                "path": "acceptance/10-spawn-acceptance-subagent.md",
                "title": {"cn": "验收阶段：派发验收 Subagent", "english": "Acceptance Stage Entry"},
                "body": {
                    "cn": [
                        "进入 `acceptance` 阶段时：读取 `acceptance/acceptance-checklist.md`，若不存在则先从模板创建；读取需求文档以了解验收标准。",
                        "派发 subagent 执行验收清单：subagent 读取需求、设计文档和验收清单，对照实际交付物核实每个清单项，将结果写入 `acceptance/acceptance-checklist.md` 和 `acceptance/sign-off.md`，并将摘要写入 `acceptance/session-memory.md`。",
                        "subagent 完成后，检查 `acceptance/sign-off.md`。",
                        "sign-off 决策为 Accepted 前，不得推进到 `done`。",
                    ],
                    "english": [
                        "On entering the `acceptance` stage: read `acceptance/acceptance-checklist.md` — if it does not exist, create it from the template; read the requirement document to understand acceptance criteria.",
                        "Dispatch a subagent to execute the acceptance checklist: subagent reads requirement, design docs, and the checklist, verifies each item against actual deliverables, writes results to `acceptance/acceptance-checklist.md` and `acceptance/sign-off.md`, and writes summary to `acceptance/session-memory.md`.",
                        "After subagent completes, review `acceptance/sign-off.md`.",
                        "Do not advance to `done` until sign-off decision is \"Accepted\".",
                    ],
                },
            },
            {
                "path": "experience-capture/10-capture-lessons.md",
                "title": {"cn": "经验沉淀节点", "english": "Experience Capture Node"},
                "body": {
                    "cn": [
                        "每个阶段完成后，先回写 `session-memory.md`。",
                        "成熟经验再融合进 `.workflow/context/experience/` 或正式规则。",
                    ],
                    "english": [
                        "After each stage, update `session-memory.md` first.",
                        "Then promote mature lessons into `.workflow/context/experience/` or formal rules.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "before-task",
        "title": {"cn": "任务执行前 Hooks", "english": "Before Task Hooks"},
        "purpose": {
            "cn": "在读取代码、写文档、写代码或执行命令前，先确认当前动作与当前节点匹配。",
            "english": "Before reading code, writing docs, coding, or running commands, confirm that the action matches the current node.",
        },
        "trigger": {
            "cn": ["准备开始具体任务前", "准备读写文件或执行命令前"],
            "english": ["before starting a concrete task", "before reading or writing files, or running commands"],
        },
        "items": [
            {
                "path": "10-route-runtime-and-meta.md",
                "title": {"cn": "先路由运行态", "english": "Route Through Runtime First"},
                "body": {
                    "cn": [
                        "任何任务都先看 `workflow-runtime.yaml` 和当前 version `meta.yaml`。",
                        "不要跳过运行态直接行动。",
                    ],
                    "english": [
                        "Every task must begin from `workflow-runtime.yaml` and the current version `meta.yaml`.",
                        "Do not act without routing through workflow state.",
                    ],
                },
            },
            {
                "path": "20-load-matched-node-hooks.md",
                "title": {"cn": "加载命中的节点 Hook", "english": "Load Matched Node Hooks"},
                "body": {
                    "cn": [
                        "先确定当前调用时机，再匹配当前 stage 对应的节点 hook。",
                        "只加载命中的 hook，不要无差别全量读取所有 hook。",
                    ],
                    "english": [
                        "Identify the current invocation timing first, then load the node hooks that match the current stage.",
                        "Load only matching hooks instead of bulk-reading every hook file.",
                    ],
                },
            },
            {
                "path": "30-reindex-experience.md",
                "title": {"cn": "执行前重索引经验", "english": "Re-index Experience Before Action"},
                "body": {
                    "cn": [
                        "阶段级任务开始前，先重新索引经验。",
                        "确认是否已有可直接复用或需要融合的成熟经验。",
                    ],
                    "english": [
                        "Before a stage-level task begins, re-index experience.",
                        "Check whether a mature lesson should be reused or fused into the current work.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "context-maintenance",
        "title": {"cn": "上下文维护 Hooks", "english": "Context Maintenance Hooks"},
        "purpose": {
            "cn": "在进入新节点、开启新子任务或上下文接近阈值时，判断是否应保留、压缩或清空上下文，并切换合适的上下文加载模式。",
            "english": "When entering a new node, starting a new subtask, or nearing token limits, decide whether context should be kept, compacted, or cleared and switch to the appropriate loading mode.",
        },
        "trigger": {
            "cn": ["进入新节点后", "开始新子任务前", "完成一个子功能模块后", "怀疑上下文已经影响下一步判断时"],
            "english": ["after entering a new node", "before a new subtask starts", "after a sub-feature/module completes", "when accumulated context may distort the next step"],
        },
        "items": [
            {
                "path": "10-classify-project-scale.md",
                "title": {"cn": "按项目规模选择上下文策略", "english": "Choose Context Strategy by Project Scale"},
                "body": {
                    "cn": [
                        "小型项目（< 50 个文件）：临界点为约 80% 标记利用率。优先使用 GPT-4o、DeepSeek 等高性价比模型，依赖全对话历史即可，无需过早清理。",
                        "中型项目（50 - 500 个文件）：临界点为约 60% 标记利用率，或每完成一个子功能模块。优先开启自动压缩，并切换 `Plan Mode` / `Act Mode`。",
                        "大型或企业级项目（> 500 个文件）：临界点为 GPT 系列约 32k 标记、Claude 系列约 150k 标记。必须采用 Repo-map + RAG 的混合策略，禁止一次性读取超过 10 个完整文件，并优先用多智能体拆模块。",
                    ],
                    "english": [
                        "Small projects (< 50 files): use about 80% token utilization as the cleanup threshold. Prefer cost-effective models such as GPT-4o or DeepSeek and keep the full conversation history unless pressure is real.",
                        "Medium projects (50 - 500 files): use about 60% token utilization, or the completion of each sub-feature/module, as the threshold. Prefer auto-compact and switch between `Plan Mode` and `Act Mode`.",
                        "Large or enterprise projects (> 500 files): use about 32k tokens for GPT-family models or 150k for Claude-family models as the threshold. Enforce a Repo-map + RAG hybrid strategy, never read more than 10 full files at once, and prefer multi-agent module isolation.",
                    ],
                },
            },
            {
                "path": "20-decide-clear-or-compact.md",
                "title": {"cn": "决定 /clear 还是 /compact", "english": "Decide Between /clear and /compact"},
                "body": {
                    "cn": [
                        "如果之前的上下文对接下来的任务已经没有影响，执行 `/clear`，然后重新读取 `workflow-runtime.yaml`、当前 version `meta.yaml` 和命中的 hooks。",
                        "如果之前的上下文仍有用，但大段细节已不再需要，执行 `/compact`，保留当前 version、stage、artifact、当前计划、未解决问题与必要路径。",
                        "不要在不清楚当前阶段、当前焦点对象和剩余验证动作时贸然清空上下文。",
                    ],
                    "english": [
                        "If previous context no longer affects the next task, run `/clear`, then re-read `workflow-runtime.yaml`, the current version `meta.yaml`, and the matched hooks.",
                        "If previous context still matters but large details no longer do, run `/compact` and retain the current version, stage, artifact, active plan, unresolved issues, and critical paths.",
                        "Do not clear context blindly when the current stage, focus object, or remaining verification work is still unclear.",
                    ],
                },
            },
            {
                "path": "30-switch-plan-and-act-mode.md",
                "title": {"cn": "切换 Plan Mode 与 Act Mode", "english": "Switch Between Plan Mode and Act Mode"},
                "body": {
                    "cn": [
                        "`Plan Mode`：只加载文件树、运行态、version `meta.yaml`、需求/变更/计划索引与最少量规则，用来判断范围、拆分工作、安排顺序。",
                        "`Act Mode`：只加载当前要改的具体文件、活跃 change / plan、验证命令与相关日志，避免把无关文件树长期留在窗口里。",
                        "从计划切到实施前，先做一次上下文维护；从一个子模块切到下一个子模块前，也先做一次上下文维护。",
                    ],
                    "english": [
                        "`Plan Mode`: load only the file tree, workflow state, version `meta.yaml`, requirement/change/plan indexes, and the smallest useful rules to scope and sequence the work.",
                        "`Act Mode`: load only the concrete files being changed, the active change / plan, verification commands, and relevant logs; do not keep the whole file tree in context.",
                        "Run one context-maintenance check before switching from planning to acting, and again before moving from one submodule to the next.",
                    ],
                },
            },
            {
                "path": "idle/10-keep-only-routing-and-user-intent.md",
                "title": {"cn": "空闲阶段只保留路由与用户意图", "english": "Idle Keeps Only Routing and User Intent"},
                "body": {
                    "cn": [
                        "在 `idle` 阶段，只保留 runtime、version `meta.yaml`、用户最新目标与必要的 hooks。",
                        "旧的实现细节、历史日志、代码片段如果与 requirement / change 尚未正式建立无关，应优先 `/clear` 或 `/compact`。",
                    ],
                    "english": [
                        "During `idle`, keep only runtime, version `meta.yaml`, the latest user intent, and necessary hooks.",
                        "Old implementation details, historical logs, and code snippets that are unrelated before requirement / change creation should be cleared or compacted first.",
                    ],
                },
            },
            {
                "path": "requirement-review/10-keep-requirement-context-only.md",
                "title": {"cn": "需求评审只保留需求上下文", "english": "Requirement Review Keeps Requirement Context Only"},
                "body": {
                    "cn": [
                        "在 `requirement_review` 阶段，只保留 requirement 文档、范围、验收边界、相关经验与必要项目事实。",
                        "与后续实现有关的大段代码、技术细节或旧方案，如果暂时不影响需求判断，应 `/compact` 或 `/clear`。",
                    ],
                    "english": [
                        "During `requirement_review`, keep only the requirement document, scope, acceptance boundaries, relevant experience, and necessary project facts.",
                        "Large implementation details, code, or old solution trails that are not needed for requirement decisions should be compacted or cleared.",
                    ],
                },
            },
            {
                "path": "changes-review/10-keep-change-split-context-only.md",
                "title": {"cn": "变更评审只保留拆分上下文", "english": "Changes Review Keeps Change-Splitting Context Only"},
                "body": {
                    "cn": [
                        "在 `changes_review` 阶段，只保留 requirement 结论、change 列表、影响范围、风险与验收方式。",
                        "已经不影响 change 拆分的 requirement 讨论细节，可优先 `/compact`。",
                    ],
                    "english": [
                        "During `changes_review`, keep only the approved requirement outcome, change list, impact scope, risks, and acceptance method.",
                        "Requirement discussion details that no longer affect change splitting should be compacted first.",
                    ],
                },
            },
            {
                "path": "plan-review/10-keep-active-plan-context-only.md",
                "title": {"cn": "计划评审只保留活跃计划上下文", "english": "Plan Review Keeps Active Plan Context Only"},
                "body": {
                    "cn": [
                        "在 `plan_review` 阶段，只保留当前 focus change、plan 文档、验证步骤、风险与必要依赖关系。",
                        "其他 change 的实现细节若不影响当前计划评审，应优先 `/compact`。",
                    ],
                    "english": [
                        "During `plan_review`, keep only the focused change, plan document, verification steps, risks, and required dependencies.",
                        "Implementation details for unrelated changes should be compacted if they do not affect the active plan review.",
                    ],
                },
            },
            {
                "path": "executing/10-keep-active-plan-and-code-context.md",
                "title": {"cn": "实施阶段只保留当前计划与代码上下文", "english": "Executing Keeps the Active Plan and Code Context"},
                "body": {
                    "cn": [
                        "在 `executing` 阶段，只保留当前活跃 plan、当前修改文件、验证命令、必要日志和未解决问题。",
                        "不要把已经完成的子模块代码、无关 change 文档、旧调试日志长期留在窗口里；完成一个子模块后优先 `/compact`，完全无关时 `/clear`。",
                    ],
                    "english": [
                        "During `executing`, keep only the active plan, currently edited files, verification commands, relevant logs, and unresolved issues.",
                        "Do not keep completed submodule code, unrelated change docs, or stale debug logs in the window; compact after each finished submodule and clear when the old context is fully irrelevant.",
                    ],
                },
            },
            {
                "path": "regression/10-keep-diagnostic-context-only.md",
                "title": {"cn": "回归阶段只保留诊断上下文", "english": "Regression Keeps Diagnostic Context Only"},
                "body": {
                    "cn": [
                        "在 `regression` 阶段，只保留失败证据、诊断结论、用户反馈和相关工作项文档。",
                        "与当前回归无关的实现历史如果不再支持问题确认，应优先 `/compact` 或 `/clear`。",
                    ],
                    "english": [
                        "During `regression`, keep only failure evidence, diagnostic conclusions, human feedback, and related work item docs.",
                        "Implementation history unrelated to the active regression should be compacted or cleared when it no longer supports problem confirmation.",
                    ],
                },
            },
            {
                "path": "done/10-clear-implementation-context-after-capture.md",
                "title": {"cn": "收尾后清理实现上下文", "english": "Clear Implementation Context After Capture"},
                "body": {
                    "cn": [
                        "在 `done` 阶段，完成最终验证、`session-memory.md` 更新和经验升级检查后，应主动清理实现期上下文。",
                        "如果接下来要转入新 requirement / change，优先 `/clear`；如果只需保留简短收尾摘要，优先 `/compact`。",
                    ],
                    "english": [
                        "During `done`, after final verification, `session-memory.md` updates, and experience-promotion checks, actively clear implementation-time context.",
                        "If the next step is a new requirement / change, prefer `/clear`; if only a short closeout summary should remain, prefer `/compact`.",
                    ],
                },
            },
            {
                "path": "testing/10-keep-testing-context-only.md",
                "title": {"cn": "测试阶段：只保留测试相关上下文", "english": "Context Maintenance: Testing Stage"},
                "body": {
                    "cn": [
                        "在 `testing` 阶段，只保留：`testing/test-plan.md`、`testing/test-cases.md`、`testing/bugs/`（仅未关闭的 bug）、`testing/session-memory.md`、`workflow-runtime.yaml` 和 version `meta.yaml`。",
                        "如果开发阶段的实现细节仍在上下文中，执行 `/clear`。",
                        "如果测试用例细节有用但占用过多空间，执行 `/compact`。",
                    ],
                    "english": [
                        "In the `testing` stage, keep only: `testing/test-plan.md`, `testing/test-cases.md`, `testing/bugs/` (open bugs only), `testing/session-memory.md`, `workflow-runtime.yaml` and version `meta.yaml`.",
                        "Use `/clear` if implementation details from the development stage are still in context.",
                        "Use `/compact` if test case details are useful but taking too much space.",
                    ],
                },
            },
            {
                "path": "acceptance/10-keep-acceptance-context-only.md",
                "title": {"cn": "验收阶段：只保留验收相关上下文", "english": "Context Maintenance: Acceptance Stage"},
                "body": {
                    "cn": [
                        "在 `acceptance` 阶段，只保留：`acceptance/acceptance-checklist.md`、`acceptance/sign-off.md`、需求文档、`acceptance/session-memory.md`、`workflow-runtime.yaml` 和 version `meta.yaml`。",
                        "在开始验收前，执行 `/clear` 以移除测试和实现上下文。",
                    ],
                    "english": [
                        "In the `acceptance` stage, keep only: `acceptance/acceptance-checklist.md`, `acceptance/sign-off.md`, the requirement document, `acceptance/session-memory.md`, `workflow-runtime.yaml` and version `meta.yaml`.",
                        "Use `/clear` to remove testing and implementation context before starting acceptance.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "during-task",
        "title": {"cn": "任务执行中 Hooks", "english": "During Task Hooks"},
        "purpose": {
            "cn": "执行过程中持续判断当前行为有没有脱离锁定节点和阶段边界。",
            "english": "During execution, keep checking whether the current behavior has drifted outside the locked node or stage boundary.",
        },
        "trigger": {
            "cn": ["执行任务进行中", "准备继续追加动作时"],
            "english": ["while a task is in progress", "before continuing with additional actions"],
        },
        "items": [
            {
                "path": "10-stay-inside-locked-node.md",
                "title": {"cn": "持续停留在锁定节点内", "english": "Stay Inside the Locked Node"},
                "body": {
                    "cn": [
                        "如果会话锁已开启，执行中不能漂移到其他 workflow 节点。",
                        "一旦发现动作已偏离，立即停止并回到当前节点语义。",
                    ],
                    "english": [
                        "If the conversation lock is active, execution must not drift into a different workflow node.",
                        "If the action has drifted, stop immediately and return to the current node semantics.",
                    ],
                },
            },
            {
                "path": "idle/10-no-implementation-prep.md",
                "title": {"cn": "空闲阶段禁止实现准备", "english": "No Implementation Preparation During Idle"},
                "body": {
                    "cn": [
                        "在 `idle` 阶段，不允许读取源码做实现准备、查找参考实现、生成代码或写业务文件。",
                        "如果用户提供的是实现型 prompt，也只能把它转成 requirement / change 的输入材料。",
                    ],
                    "english": [
                        "During `idle`, do not read source code for implementation prep, search for reference implementations, generate code, or write business files.",
                        "If the user provides an implementation-oriented prompt, treat it only as input for a requirement / change.",
                    ],
                },
            },
            {
                "path": "requirement-review/10-no-source-code.md",
                "title": {"cn": "需求节点禁止改源码", "english": "No Source Changes in Requirement Review"},
                "body": {
                    "cn": [
                        "在 `requirement_review` 阶段，不允许写生产代码或改业务源码。",
                        "允许补 requirement 文档、讨论范围和验收边界。",
                    ],
                    "english": [
                        "During `requirement_review`, do not write production code or modify business source files.",
                        "Requirement document updates, scope discussion, and acceptance clarification are allowed.",
                    ],
                },
            },
            {
                "path": "requirement-review/20-no-auto-stage-advance.md",
                "title": {"cn": "需求评审中禁止自动推进阶段", "english": "No Automatic Stage Advance During Requirement Review"},
                "body": {
                    "cn": [
                        "在 `requirement_review` 阶段，不要自动执行 `harness next`、自动拆 `change` 或自动生成 `plan`。",
                        "如果用户给的是实现细节，也只允许把它吸收进 requirement，随后等待用户确认。",
                    ],
                    "english": [
                        "During `requirement_review`, do not automatically run `harness next`, split changes, or generate plans.",
                        "If the human provides implementation details, absorb them into the requirement and then wait for confirmation.",
                    ],
                },
            },
            {
                "path": "changes-review/20-no-auto-stage-advance.md",
                "title": {"cn": "变更评审中禁止自动推进阶段", "english": "No Automatic Stage Advance During Changes Review"},
                "body": {
                    "cn": [
                        "在 `changes_review` 阶段，不要自动执行 `harness next`、自动生成 `plan` 或自动推进到计划评审。",
                        "如果用户补充细节，也只允许把它吸收进 change 文档，然后等待用户确认。",
                    ],
                    "english": [
                        "During `changes_review`, do not automatically run `harness next`, generate plans, or advance into plan review.",
                        "If the human adds details, absorb them into the change documents and then wait for confirmation.",
                    ],
                },
            },
            {
                "path": "plan-review/20-no-auto-stage-advance.md",
                "title": {"cn": "计划评审中禁止自动推进阶段", "english": "No Automatic Stage Advance During Plan Review"},
                "body": {
                    "cn": [
                        "在 `plan_review` 阶段，不要自动执行 `harness next`、自动开始编码或自动进入执行阶段。",
                        "如果用户补充实施细节，也只允许把它吸收进 plan，然后等待用户确认。",
                    ],
                    "english": [
                        "During `plan_review`, do not automatically run `harness next`, start coding, or enter execution.",
                        "If the human adds implementation details, absorb them into the plan and then wait for confirmation.",
                    ],
                },
            },
            {
                "path": "ready-for-execution/10-no-implementation-before-confirmation.md",
                "title": {"cn": "执行确认前禁止开始实现", "english": "No Implementation Before Execution Confirmation"},
                "body": {
                    "cn": [
                        "在 `ready_for_execution` 阶段，不要读取源码做实现准备、不要写生产代码、不要启动实施任务。",
                        "只有用户显式确认执行或运行 `harness next --execute` 后，才允许进入 `executing`。",
                    ],
                    "english": [
                        "During `ready_for_execution`, do not read source code for implementation prep, write production code, or start execution tasks.",
                        "Only after explicit human approval or `harness next --execute` may the workflow enter `executing`.",
                    ],
                },
            },
            {
                "path": "done/10-no-closeout-before-lesson-capture.md",
                "title": {"cn": "经验未沉淀前禁止直接收尾", "english": "No Closeout Before Lesson Capture"},
                "body": {
                    "cn": [
                        "在 `done` 阶段，不要在 `session-memory.md` 仍为空或经验尚未检查时直接结束对话或宣称任务闭环。",
                        "先补齐经验沉淀，再做最终完成表达。",
                    ],
                    "english": [
                        "During `done`, do not end the task or claim closure while `session-memory.md` is still empty or lesson promotion has not been checked.",
                        "Capture lessons first, then make the final completion claim.",
                    ],
                },
            },
            {
                "path": "regression/10-no-direct-rework.md",
                "title": {"cn": "回归中禁止直接返工", "english": "No Direct Rework During Regression"},
                "body": {
                    "cn": [
                        "回归中先做问题确认，不要直接开始修代码。",
                        "只有确认问题并转换成 change / requirement 后，才能进入正常修复流。",
                    ],
                    "english": [
                        "During regression, confirm the problem first instead of jumping directly into code changes.",
                        "Only after conversion into a change or requirement may the normal fix flow begin.",
                    ],
                },
            },
            {
                "path": "executing/10-follow-plan-and-verify.md",
                "title": {"cn": "实施中遵循计划与验证", "english": "Follow Plan and Verification While Executing"},
                "body": {
                    "cn": [
                        "进入 `executing` 后，实施步骤和验证步骤要配对推进。",
                        "不要把执行阶段变成无计划的自由编码。",
                    ],
                    "english": [
                        "Once in `executing`, implementation and verification steps should advance in pairs.",
                        "Do not turn execution into unplanned free-form coding.",
                    ],
                },
            },
            {
                "path": "testing/10-subagent-reports-to-session-memory.md",
                "title": {"cn": "测试阶段：Subagent 汇报到 session-memory", "english": "Testing Stage: Subagent Reporting"},
                "body": {
                    "cn": [
                        "在 `testing` 阶段，subagent 必须将所有测试结果写入 `testing/test-cases.md`（更新 Status 列）。",
                        "每个发现的 bug 必须使用 bug 模板写入 `testing/bugs/<bug-id>.md`。",
                        "subagent 退出前必须将摘要写入 `testing/session-memory.md`。",
                        "主 agent 通过读取 `testing/session-memory.md` 来决定下一步。",
                    ],
                    "english": [
                        "Subagents must write all test results to `testing/test-cases.md` (update Status column).",
                        "Each discovered bug must be written to `testing/bugs/<bug-id>.md` using the bug template.",
                        "Subagents must write a summary to `testing/session-memory.md` before exiting.",
                        "Main agent reads `testing/session-memory.md` to determine next steps.",
                    ],
                },
            },
            {
                "path": "acceptance/10-checklist-driven-only.md",
                "title": {"cn": "验收阶段：仅以清单为驱动", "english": "Acceptance Stage: Checklist-Driven Only"},
                "body": {
                    "cn": [
                        "在 `acceptance` 阶段，所有核验必须遵循 `acceptance/acceptance-checklist.md` 中的条目。",
                        "不得跳过任何清单项。",
                        "每个条目必须注明所依据的文档或制品，并记录通过/失败及备注。",
                        "所有条目记录完成后，才能填写 `acceptance/sign-off.md`。",
                    ],
                    "english": [
                        "All verification must follow items in `acceptance/acceptance-checklist.md`.",
                        "Do not skip checklist items.",
                        "Each item must reference the document or artifact used as basis; record pass/fail with notes.",
                        "Only after all items are recorded should `acceptance/sign-off.md` be filled.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "before-human-input",
        "title": {"cn": "向人索要输入前 Hooks", "english": "Before Human Input Hooks"},
        "purpose": {
            "cn": "只有在本机证据已收集且仍然缺外部信息时，才允许向用户索要输入。",
            "english": "Ask the human for input only after local evidence has been collected and external information is still missing.",
        },
        "trigger": {
            "cn": ["准备向用户索要配置、数据、账号、环境信息前"],
            "english": ["before asking the human for configuration, data, credentials, or environment details"],
        },
        "items": [
            {
                "path": "05-check-mcp-registry.md",
                "title": {"cn": "先查 MCP 注册表", "english": "Check MCP Registry First"},
                "body": {
                    "cn": [
                        "向用户索要外部信息前，先查 `.workflow/context/mcp-registry.yaml`。",
                        "如果注册表里有匹配的 MCP，优先调用 MCP 获取信息。",
                        "如果没有匹配但项目依赖提示可能有可用 MCP，建议用户安装。",
                    ],
                    "english": [
                        "Before asking the human for external information, check `.workflow/context/mcp-registry.yaml` first.",
                        "If a matching MCP exists in the registry, prefer calling the MCP to get the information.",
                        "If no match exists but project dependencies suggest a usable MCP, recommend installation.",
                    ],
                },
            },
            {
                "path": "10-local-debug-first.md",
                "title": {"cn": "本机调试信息优先", "english": "Local Debug Evidence First"},
                "body": {
                    "cn": [
                        "启动日志、编译输出、测试失败堆栈、运行时报错，先由 AI 自查。",
                        "不要先让用户代看本机日志。",
                    ],
                    "english": [
                        "Startup logs, compile output, test failures, and runtime errors must be inspected by the AI first.",
                        "Do not ask the human to inspect local logs first.",
                    ],
                },
            },
            {
                "path": "20-required-inputs-template-first.md",
                "title": {"cn": "先写 required-inputs 模板", "english": "Fill the required-inputs Template First"},
                "body": {
                    "cn": [
                        "如果仍需用户提供外部信息，先填写当前 change `regression/required-inputs.md`。",
                        "不允许跳过模板直接在对话里临时发问。",
                    ],
                    "english": [
                        "If external information is still required, fill the current change `regression/required-inputs.md` first.",
                        "Do not skip the template and ask ad hoc questions in chat.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "after-task",
        "title": {"cn": "任务执行后 Hooks", "english": "After Task Hooks"},
        "purpose": {
            "cn": "任务结束后立刻复盘并沉淀经验，避免丢失新的约束和失败路径。",
            "english": "Review and capture lessons immediately after a task so new constraints and failed paths are not lost.",
        },
        "trigger": {
            "cn": ["一个阶段任务结束后", "准备结束当前动作前"],
            "english": ["after a stage-level task ends", "before fully closing the current action"],
        },
        "items": [
            {
                "path": "10-update-session-memory.md",
                "title": {"cn": "先更新工作记忆", "english": "Update Working Memory First"},
                "body": {
                    "cn": [
                        "先把新增经验、失败路径、被纠正结论写入 `session-memory.md`。",
                        "不要把短期状态直接写进长期记忆。",
                    ],
                    "english": [
                        "Write new lessons, failed paths, and corrections into `session-memory.md` first.",
                        "Do not put short-lived task state directly into durable memory.",
                    ],
                },
            },
            {
                "path": "20-promote-mature-lessons.md",
                "title": {"cn": "升级成熟经验", "english": "Promote Mature Lessons"},
                "body": {
                    "cn": [
                        "已经稳定、可复用的经验，再升级进 `.workflow/context/experience/` 或正式规则。",
                        "每个阶段都要判断是否值得融合成熟经验。",
                    ],
                    "english": [
                        "Promote only stable, reusable lessons into `.workflow/context/experience/` or formal rules.",
                        "After each stage, decide whether mature experience should now be fused into the workflow.",
                    ],
                },
            },
        ],
    },
    {
        "slug": "before-complete",
        "title": {"cn": "完成前 Hooks", "english": "Before Completion Hooks"},
        "purpose": {
            "cn": "在声称完成前，强制执行构建、启动和失败回归门禁。",
            "english": "Before claiming completion, enforce compile, startup, and regression gates.",
        },
        "trigger": {
            "cn": ["准备宣称 change 完成前", "准备宣称 requirement 完成前", "准备宣称 version 完成前"],
            "english": ["before claiming a change is complete", "before claiming a requirement is complete", "before claiming a version is complete"],
        },
        "items": [
            {
                "path": "10-require-mvn-compile.md",
                "title": {"cn": "change 完成前必须编译", "english": "Changes Require mvn compile"},
                "body": {
                    "cn": [
                        "每个 change 完成前，必须执行并记录 `mvn compile`。",
                        "没有编译证据时，不允许宣称 change 完成。",
                    ],
                    "english": [
                        "Every completed change must execute and record `mvn compile`.",
                        "Do not claim a change is complete without compile evidence.",
                    ],
                },
            },
            {
                "path": "20-require-startup-validation.md",
                "title": {"cn": "requirement 完成前必须启动成功", "english": "Requirements Need Startup Validation"},
                "body": {
                    "cn": [
                        "每个 requirement 完成前，必须执行并记录项目启动成功验证。",
                        "没有启动验证证据时，不允许宣称 requirement 完成。",
                    ],
                    "english": [
                        "Every completed requirement must execute and record successful project startup validation.",
                        "Do not claim a requirement is complete without startup validation evidence.",
                    ],
                },
            },
            {
                "path": "30-failure-to-regression.md",
                "title": {"cn": "失败必须转 regression", "english": "Failures Must Enter Regression"},
                "body": {
                    "cn": [
                        "如果编译失败或启动失败，不允许绕过，必须进入 regression。",
                        "失败不应被包装成完成。",
                    ],
                    "english": [
                        "If compilation or startup fails, do not bypass it; enter regression first.",
                        "A failed gate must not be repackaged as completion.",
                    ],
                },
            },
            {
                "path": "40-require-session-memory-sync.md",
                "title": {"cn": "完成前必须同步 session-memory", "english": "Completion Requires session-memory Sync"},
                "body": {
                    "cn": [
                        "在宣称 change、requirement 或 version 完成前，先更新相关 change 的 `session-memory.md`。",
                        "没有经验沉淀记录时，不允许宣称工作已完整完成。",
                    ],
                    "english": [
                        "Before claiming a change, requirement, or version is complete, update the related change `session-memory.md` first.",
                        "Do not claim the work is fully complete without lesson capture records.",
                    ],
                },
            },
            {
                "path": "50-require-experience-promotion-check.md",
                "title": {"cn": "完成前必须检查成熟经验升级", "english": "Completion Requires an Experience Promotion Check"},
                "body": {
                    "cn": [
                        "在完成前，检查本次任务是否产生了可升级进 `.workflow/context/experience/` 或正式规则的成熟经验。",
                        "即使最终没有升级，也要完成一次显式检查。",
                    ],
                    "english": [
                        "Before completion, check whether this task produced mature lessons that should be promoted into `.workflow/context/experience/` or formal rules.",
                        "Even if nothing is promoted, perform the check explicitly.",
                    ],
                },
            },
            {
                "path": "testing/10-require-all-cases-recorded.md",
                "title": {"cn": "完成测试阶段前：所有用例必须已记录", "english": "Before Completing Testing Stage"},
                "body": {
                    "cn": [
                        "验证 `testing/test-cases.md` 中所有测试用例已有记录状态（非 pending）。",
                        "验证没有任何测试用例状态为 fail。",
                        "验证 `testing/bugs/` 中所有 bug 状态为 Fixed 或 Verified。",
                        "验证 `testing/session-memory.md` 已更新为最终摘要。",
                        "如有任何条件未满足，不得推进——修复问题或将其记录为已知风险。",
                    ],
                    "english": [
                        "Verify that ALL test cases in `testing/test-cases.md` have a recorded status (not \"pending\").",
                        "Verify that zero test cases have status \"fail\".",
                        "Verify that all bugs in `testing/bugs/` have status \"Fixed\" or \"Verified\".",
                        "Verify that `testing/session-memory.md` has been updated with the final summary.",
                        "If any condition is not met, do not advance — fix the issue or document it as a known risk.",
                    ],
                },
            },
            {
                "path": "acceptance/10-require-sign-off.md",
                "title": {"cn": "完成验收阶段前：必须有 sign-off", "english": "Before Completing Acceptance Stage"},
                "body": {
                    "cn": [
                        "验证 `acceptance/acceptance-checklist.md` 所有条目已填写。",
                        "验证 `acceptance/sign-off.md` 存在且决策为 Accepted。",
                        "验证 `acceptance/session-memory.md` 已更新。",
                        "将相关经验沉淀到 `.workflow/context/experience/stage/acceptance.md`。",
                        "如果 sign-off 为 Rejected，改为启动 `harness regression` 而非推进。",
                    ],
                    "english": [
                        "Verify that `acceptance/acceptance-checklist.md` has all items filled.",
                        "Verify that `acceptance/sign-off.md` exists and decision is \"Accepted\".",
                        "Verify that `acceptance/session-memory.md` has been updated.",
                        "Capture any lessons into `.workflow/context/experience/stage/acceptance.md`.",
                        "If sign-off is \"Rejected\", start `harness regression` instead of advancing.",
                    ],
                },
            },
        ],
    },
]


def render_hooks_index(language: str) -> str:
    is_cn = normalize_language(language) == "cn"
    lines = [
        "# Hooks 目录" if is_cn else "# Hooks Directory",
        "",
        "## 目标" if is_cn else "## Purpose",
        "",
        (
            "本目录按“调用时机”组织 hooks。Agent 先识别当前调用时机，再读取对应的时机说明文档和命中的 hook 文件。"
            if is_cn
            else "This directory organizes hooks by invocation timing. The agent should identify the current timing first, then read the timing overview and the matching hook files."
        ),
        "",
        "## 匹配顺序" if is_cn else "## Matching Order",
        "",
        "1. 读取 `.workflow/context/rules/workflow-runtime.yaml`" if is_cn else "1. Read `.workflow/context/rules/workflow-runtime.yaml`",
        "2. 根据 `current_version` 读取当前 version `meta.yaml`" if is_cn else "2. Use `current_version` to read the active version `meta.yaml`",
        "3. 判断当前调用时机，例如 `session-start`、`before-reply`、`before-task`、`context-maintenance`、`during-task`、`before-human-input`、`after-task`、`before-complete`" if is_cn else "3. Identify the current invocation timing, such as `session-start`, `before-reply`, `before-task`, `context-maintenance`, `during-task`, `before-human-input`, `after-task`, or `before-complete`",
        "4. 读取对应的 `<timing>.md` 说明文档" if is_cn else "4. Read the matching `<timing>.md` overview document",
        "5. 按编号顺序读取 `<timing>/` 下的通用 hook 文件" if is_cn else "5. Read the general hook files under `<timing>/` in numeric order",
        "6. 如果存在当前节点对应的子目录，例如 `requirement-review/`、`executing/`、`regression/`，继续按编号加载" if is_cn else "6. If there is a stage-specific subdirectory such as `requirement-review/`, `executing/`, or `regression/`, load those files in numeric order as well",
        "7. 任一硬门禁命中时，立即停止当前动作" if is_cn else "7. If any hard gate blocks the action, stop immediately",
        "",
        "## 调用时机" if is_cn else "## Timings",
        "",
    ]
    for timing in HOOK_TIMINGS:
        title = str(localized_text(timing["title"], language))
        purpose = str(localized_text(timing["purpose"], language))
        lines.append(f"- `{timing['slug']}.md`：{title}，{purpose}" if is_cn else f"- `{timing['slug']}.md`: {title}. {purpose}")
        lines.append(
            f"- `{timing['slug']}/`：该调用时机下的具体 hook 文件与节点子目录"
            if is_cn
            else f"- `{timing['slug']}/`: concrete hook files and node subdirectories for that timing"
        )
    return "\n".join(lines) + "\n"


def render_hook_timing_doc(timing: dict[str, object], language: str) -> str:
    is_cn = normalize_language(language) == "cn"
    title = str(localized_text(timing["title"], language))
    purpose = str(localized_text(timing["purpose"], language))
    triggers = [str(item) for item in localized_text(timing["trigger"], language)]
    items = [str(item["path"]) for item in timing["items"]]  # type: ignore[index]
    lines = [f"# {title}", ""]
    lines.append("## 作用" if is_cn else "## Purpose")
    lines.append("")
    lines.append(purpose)
    lines.append("")
    lines.append("## 触发时机" if is_cn else "## Trigger")
    lines.append("")
    for trigger in triggers:
        lines.append(f"- {trigger}")
    lines.append("")
    lines.append("## 加载方式" if is_cn else "## Loading Order")
    lines.append("")
    if is_cn:
        lines.extend(
            [
                f"1. 先读取 `.workflow/context/hooks/{timing['slug']}.md`",
                f"2. 再按编号顺序读取 `.workflow/context/hooks/{timing['slug']}/` 下的通用 hook",
                "3. 如果存在当前 stage 或当前节点对应的子目录，也继续按编号读取",
                "4. 命中硬门禁时立即停止",
            ]
        )
    else:
        lines.extend(
            [
                f"1. Read `.workflow/context/hooks/{timing['slug']}.md` first",
                f"2. Then read the general hooks under `.workflow/context/hooks/{timing['slug']}/` in numeric order",
                "3. If a subdirectory matches the current stage or node, read those files in numeric order too",
                "4. Stop immediately if a hard gate blocks the action",
            ]
        )
    lines.append("")
    lines.append("## 目录内容" if is_cn else "## Contents")
    lines.append("")
    for item in items:
        lines.append(f"- `{item}`")
    return "\n".join(lines) + "\n"


def render_hook_item_doc(timing_slug: str, item: dict[str, object], language: str) -> str:
    title = str(localized_text(item["title"], language))
    body = [str(line) for line in localized_text(item["body"], language)]
    lines = [f"# {title}", "", f"`{timing_slug}`", "", "## Rules", ""]
    for line in body:
        lines.append(f"- {line}")
    return "\n".join(lines) + "\n"


def hook_managed_contents(language: str) -> dict[str, str]:
    managed: dict[str, str] = {".workflow/context/hooks/README.md": render_hooks_index(language)}
    for timing in HOOK_TIMINGS:
        slug = str(timing["slug"])
        managed[f".workflow/context/hooks/{slug}.md"] = render_hook_timing_doc(timing, language)
        for item in timing["items"]:  # type: ignore[index]
            path = str(item["path"])
            managed[f".workflow/context/hooks/{slug}/{path}"] = render_hook_item_doc(slug, item, language)
    return managed


def write_if_missing(path: Path, content: str, created: list[str], skipped: list[str]) -> None:
    if path.exists():
        skipped.append(str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    created.append(str(path))


def _copy_tree(source: Path, target: Path) -> None:
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


def _project_skill_targets(root: Path) -> list[Path]:
    from harness_workflow.backup import read_platforms_config
    config = read_platforms_config(str(root))
    enabled = config.get("enabled", [])

    targets = []
    if "codex" in enabled:
        targets.append(root / ".codex" / "skills" / "harness")
    if "cc" in enabled:
        targets.append(root / ".claude" / "skills" / "harness")
    if "qoder" in enabled:
        targets.append(root / ".qoder" / "skills" / "harness")
    # kimi 不通过 install_local_skills 安装，通过其他机制处理
    return targets


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _matches_platform_pattern(file_path: str, pattern: str) -> bool:
    """Check if file path matches a platform pattern.

    Args:
        file_path: Relative file path
        pattern: Platform pattern (may end with / for directory prefix)

    Returns:
        Whether the path matches
    """
    if pattern.endswith("/"):
        return file_path.startswith(pattern)
    return file_path == pattern


def _load_json(path: Path, default: dict[str, str]) -> dict[str, str]:
    if not path.exists():
        return dict(default)
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = dict(default)
    merged.update({str(key): str(value) for key, value in data.items()})
    return merged


def load_config(root: Path) -> dict[str, str]:
    config = _load_json(root / CONFIG_PATH, DEFAULT_CONFIG)
    config["language"] = normalize_language(config.get("language"))
    return config


def save_config(root: Path, config: dict[str, str]) -> None:
    path = root / CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_CONFIG)
    payload.update(config)
    payload["language"] = normalize_language(payload.get("language"))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_config(root: Path) -> dict[str, str]:
    config = load_config(root)
    save_config(root, config)
    return config


def _load_managed_state(root: Path) -> dict[str, str]:
    path = root / MANAGED_STATE_PATH
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(key): str(value) for key, value in data.get("managed_files", {}).items()}


def _save_managed_state(root: Path, managed_files: dict[str, str]) -> None:
    path = root / MANAGED_STATE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tool_version": __version__,
        "managed_files": dict(sorted(managed_files.items())),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _required_dirs(root: Path) -> list[Path]:
    # branch 解析失败兜底 "main"；helper 此处调用安全，因 _required_dirs 仅在 init / update 路径被触发。
    # 注意：legacy `.workflow/flow/requirements` 保留是为了过渡期不破坏老仓读取；
    # 运行时读取只走 `resolve_requirement_root`，init 侧同时建 legacy + 新路径以避免"写新路径、
    # 读旧路径"或"新仓无 legacy → helper 降级误判"两种情况。
    branch = _get_git_branch(root) or "main"
    return [
        root / ".workflow" / "state",
        root / ".workflow" / "state" / "requirements",
        root / ".workflow" / "state" / "sessions",
        root / ".workflow" / "state" / "experience",
        root / ".workflow" / "flow",
        root / ".workflow" / "flow" / "requirements",
        root / "artifacts" / branch / "requirements",
        root / ".workflow" / "constraints",
        root / ".workflow" / "evaluation",
        root / ".workflow" / "context" / "roles",
        root / ".workflow" / "context" / "team",
        root / ".workflow" / "context" / "project",
        root / ".workflow" / "context" / "experience",
        root / ".workflow" / "context" / "experience" / "stage",
        root / ".workflow" / "context" / "experience" / "tool",
        root / ".workflow" / "context" / "experience" / "risk",
        root / ".workflow" / "tools",
        root / ".workflow" / "tools" / "catalog",
        root / HARNESS_DIR,
    ]


def _experience_stub(title: str, path: str, language: str) -> str:
    """Return a minimal placeholder for a new experience file (write_if_missing mode)."""
    if language == "cn":
        return (
            f"# {title}\n\n"
            f"> 经验文件占位。请根据实际项目经验补充内容。\n\n"
            f"## 核心约束\n\n<!-- 在此记录必须遵守的约束 -->\n\n"
            f"## 最佳实践\n\n<!-- 在此记录推荐做法 -->\n\n"
            f"## 常见错误\n\n<!-- 在此记录常见错误 -->\n"
        )
    return (
        f"# {title}\n\n"
        f"> Placeholder experience file. Fill in based on actual project lessons.\n\n"
        f"## Key Constraints\n\n<!-- Record must-follow constraints here -->\n\n"
        f"## Best Practices\n\n<!-- Record recommended approaches here -->\n\n"
        f"## Common Mistakes\n\n<!-- Record common errors here -->\n"
    )


def _managed_file_contents(root: Path, language: str, include_agents: bool, include_claude: bool) -> dict[str, str]:
    repo_name = root.name
    managed = _scaffold_v2_file_contents(
        root,
        include_agents=include_agents,
        include_claude=include_claude,
        language=language,
    )
    managed[".qoder/rules/harness-workflow.md"] = render_template("qoder-rule.md.tmpl", repo_name, language)
    for command in COMMAND_DEFINITIONS:
        markdown = render_agent_command(command["name"], command["cli"], command["hint"], language)
        managed[f".qoder/commands/{command['name']}.md"] = markdown
        managed[f".claude/commands/{command['name']}.md"] = markdown
        managed[f".codex/skills/{command['name']}/SKILL.md"] = render_codex_command_skill(
            command["name"], command["cli"], language
        )
        managed[f".kimi/skills/{command['name']}/SKILL.md"] = render_kimi_command_skill(
            command["name"], command["cli"], language
        )
    return managed


def _refresh_managed_state(
    root: Path,
    managed_contents: dict[str, str],
    existing_state: dict[str, str] | None = None,
) -> dict[str, str]:
    state = dict(existing_state or {})
    for relative, content in managed_contents.items():
        path = root / relative
        if path.exists() and path.read_text(encoding="utf-8") == content:
            state[relative] = _managed_hash(content)
    return state


def install_local_skills(root: Path, force: bool = False) -> list[Path]:
    installed: list[Path] = []
    for target in _project_skill_targets(root):
        if target.exists():
            if force:
                shutil.rmtree(target)
            else:
                installed.append(target)
                continue
        target.mkdir(parents=True, exist_ok=True)
        _copy_tree(Path(str(SKILL_ROOT)), target)
        installed.append(target)
    return installed


def ensure_harness_root(root: Path) -> dict[str, str]:
    required = [root / ".workflow", root / ".workflow" / "context"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Harness workspace is missing. Run `harness install` or `harness init` first. Missing: {', '.join(missing)}")
    return ensure_config(root)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug


def _path_slug(title: str, max_len: int = 60) -> str:
    """bugfix-3：为 create_requirement / create_bugfix 生成路径安全的 slug。

    约束：
    - 走共享 ``slugify_preserve_unicode``，过滤 `/` 等非法路径字符；
    - 长度上限 ``max_len``（默认 60），截断后再 ``strip('-')``；
    - 全部字符被过滤 / 空输入 → 返回空串，由调用方回退到 id-only。
    """
    if not title:
        return ""
    slug = slugify_preserve_unicode(title)
    if not slug:
        return ""
    return slug[:max_len].strip("-")


def resolve_artifact_id(title: str, language: str) -> str:
    title = title.strip()
    if normalize_language(language) == "cn":
        return title
    slug = slugify(title)
    if slug:
        return slug
    fallback = re.sub(r"\s+", "-", title).strip("-")
    return fallback or title


def resolve_title_and_id(
    positional: str | None,
    id_flag: str | None,
    title_flag: str | None,
    language: str,
) -> tuple[str, str]:
    if positional:
        title = positional.strip()
        return title, resolve_artifact_id(title, language)
    if title_flag:
        title = title_flag.strip()
        return title, (id_flag.strip() if id_flag else resolve_artifact_id(title, language))
    if id_flag:
        identifier = id_flag.strip()
        return identifier, identifier
    raise SystemExit("A title or id is required.")


def load_item_meta(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    payload: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                payload[key.strip()] = json.loads(value)
            except json.JSONDecodeError:
                payload[key.strip()] = value.strip('"')
        else:
            payload[key.strip()] = value
    return payload


def save_item_meta(path: Path, payload: dict[str, str]) -> None:
    ordered_keys = [key for key in ITEM_META_ORDER if key in payload] + [key for key in payload if key not in ITEM_META_ORDER]
    lines = [f"{key}: {json.dumps(str(payload.get(key, '')), ensure_ascii=False)}" for key in ordered_keys]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replace_in_file(path: Path, replacements: dict[str, str]) -> None:
    if not path.exists() or not replacements:
        return
    text = path.read_text(encoding="utf-8")
    updated = text
    for source, target in replacements.items():
        updated = updated.replace(source, target)
    if updated != text:
        path.write_text(updated, encoding="utf-8")


def update_item_meta(path: Path, updates: dict[str, str]) -> None:
    payload = load_item_meta(path)
    payload.update(updates)
    save_item_meta(path, payload)


def remap_identifier_list(values: list[object], mapping: dict[str, str]) -> list[str]:
    return [mapping.get(str(value), str(value)) for value in values]


def remap_meta_strings(meta: dict[str, object], replacements: dict[str, str]) -> dict[str, object]:
    payload = dict(meta)
    for field in ("current_task", "next_action", "assistant_prompt"):
        current = str(payload.get(field, ""))
        for source, target in replacements.items():
            current = current.replace(source, target)
        payload[field] = current
    return payload


def ensure_workflow_state(root: Path) -> tuple[dict[str, str], dict[str, object]]:
    config = ensure_harness_root(root)
    runtime = load_requirement_runtime(root)
    save_requirement_runtime(root, runtime)
    return config, runtime


def record_feedback_event(root: Path, event_type: str, data: dict[str, object]) -> None:
    """Append a single feedback event to .harness/feedback.jsonl. Never raises."""
    try:
        feedback_dir = root / FEEDBACK_DIR
        feedback_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "data": data,
        }
        with open(root / FEEDBACK_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001
        pass


def set_regression_mode(runtime: dict[str, object], regression_id: str = "") -> dict[str, object]:
    payload = dict(runtime)
    payload["mode"] = "regression" if regression_id else "normal"
    payload["current_regression"] = regression_id
    return payload


def set_conversation_mode(
    runtime: dict[str, object],
    *,
    conversation_mode: str,
) -> dict[str, object]:
    payload = dict(runtime)
    payload["conversation_mode"] = conversation_mode
    if conversation_mode != "harness":
        payload["locked_requirement"] = ""
        payload["locked_stage"] = ""
    return payload


def exit_harness_mode(runtime: dict[str, object]) -> dict[str, object]:
    return set_conversation_mode(runtime, conversation_mode="open")


def select_focus_change(meta: dict[str, object]) -> str:
    current_kind = str(meta.get("current_artifact_kind", ""))
    current_id = str(meta.get("current_artifact_id", ""))
    if current_kind in {"change", "plan"} and current_id:
        return current_id
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    return change_ids[-1] if change_ids else ""


def apply_stage_transition(meta: dict[str, object], *, execute: bool = False, fast_forward: bool = False) -> dict[str, object]:
    payload = dict(meta)
    stage = str(payload.get("stage", "idle"))
    requirement_id = str(payload.get("current_artifact_id", "")) if str(payload.get("current_artifact_kind", "")) == "requirement" else ""
    focus_change = select_focus_change(payload)

    now_iso = datetime.now(timezone.utc).isoformat()

    if fast_forward:
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Confirm whether to start implementation",
                "next_action": "Run `harness next --execute` after the final review.",
                "suggested_skill": "",
                "assistant_prompt": "Review the current requirement, changes, and plan documents. Do not start coding until the human confirms execution.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "requirement_review":
        payload.update(
            {
                "stage": "changes_review",
                "status": "review",
                "current_task": f"Split reviewed requirement {requirement_id or '(current requirement)'} into changes",
                "next_action": "Create or refine change documents, then run `harness next`.",
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to decompose the approved requirement into independently deliverable changes, create or update the change documents, and stop for human review before advancing.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "changes_review":
        if not focus_change:
            raise SystemExit("No changes exist yet. Create at least one `harness change` before advancing.")
        payload.update(
            {
                "stage": "plan_review",
                "status": "review",
                "current_task": f"Draft and review the plan for change {focus_change}",
                "next_action": f"Generate or review the plan for {focus_change}, then run `harness next`.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
                "suggested_skill": "writing-plans",
                "assistant_prompt": f"Use writing-plans to turn change {focus_change} into a model-executable implementation plan, then stop for human review.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "plan_review":
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Review complete. Waiting for execution confirmation",
                "next_action": "Run `harness next --execute` to start implementation.",
                "suggested_skill": "",
                "assistant_prompt": "Ask the human to confirm execution. Do not start implementation before explicit confirmation.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "ready_for_execution":
        if not execute:
            raise SystemExit("Current version is ready_for_execution. Run `harness next --execute` to confirm execution.")
        payload.update(
            {
                "stage": "executing",
                "status": "executing",
                "current_task": f"Execute approved work for {focus_change or 'the current version'}",
                "next_action": "Implement the approved plan and keep version state updated.",
                "current_artifact_kind": "change" if focus_change else str(payload.get("current_artifact_kind", "")),
                "current_artifact_id": focus_change or str(payload.get("current_artifact_id", "")),
                "suggested_skill": "executing-plans",
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan. Keep documents and verification in sync while executing. As each task settles, update the relevant `session-memory.md` instead of postponing lesson capture until the very end.",
                "approval_required": False,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "executing":
        payload.update(
            {
                "stage": "testing",
                "status": "in_progress",
                "current_task": "设计并执行测试用例",
                "next_action": "Subagent 执行测试计划，结果写入 testing/test-cases.md 和 progress.yaml",
                "suggested_skill": "subagent-driven-development",
                "assistant_prompt": "Use subagent-driven-development to design and execute test cases for all completed changes. Record results in testing/test-cases.md and update progress.yaml. If bugs are found, use `harness regression --testing` to roll back to testing stage and document the bug.",
                "approval_required": False,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "testing":
        payload.update(
            {
                "stage": "acceptance",
                "status": "in_progress",
                "current_task": "依据文档执行人工验收",
                "next_action": "对照 acceptance-checklist.md 逐项验收，结果写入 acceptance/sign-off.md",
                "suggested_skill": "verification-before-completion",
                "assistant_prompt": "Execute acceptance testing based on the acceptance-checklist.md. Record the sign-off results in acceptance/sign-off.md. Verify each acceptance criterion and stop for human confirmation before advancing.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "acceptance":
        payload.update(
            {
                "stage": "done",
                "status": "done",
                "current_task": "Execution finished. Summarize and verify outcomes",
                "next_action": "Verify `mvn compile` for each completed change, successful project startup for the completed requirement, update the related `session-memory.md`, and check whether mature lessons should be promoted before closing. If verification fails, start `harness regression \"<issue>\"`.",
                "suggested_skill": "verification-before-completion",
                "assistant_prompt": "Run final verification. Each completed change must include `mvn compile`. Completed requirement work must include successful project startup validation. Before claiming completion, update the related `session-memory.md` and explicitly check whether mature lessons should be promoted into `.workflow/context/experience/` or formal rules. If compilation or startup fails, stop and start `harness regression \"<issue>\"`. If user input is needed, fill the related change `regression/required-inputs.md` template and wait for the human response.",
                "approval_required": False,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    raise SystemExit("No workflow stage is active yet. Start with `harness requirement <title>`.")


def resolve_requirement_reference(requirements_dir: Path, reference: str, language: str) -> Path | None:
    direct = requirements_dir / reference
    if direct.exists():
        return direct
    derived = requirements_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    # Prefix match: "req-05" matches "req-05-功能扩展"
    if requirements_dir.exists():
        for child in sorted(requirements_dir.iterdir()):
            if child.is_dir() and child.name.startswith(reference + "-"):
                return child
    return None


def resolve_change_reference(changes_dir: Path, reference: str, language: str) -> Path | None:
    direct = changes_dir / reference
    if direct.exists():
        return direct
    derived = changes_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    # Prefix match: "chg-01" matches "chg-01-xxx"
    if changes_dir.exists():
        for child in sorted(changes_dir.iterdir()):
            if child.is_dir() and child.name.startswith(reference + "-"):
                return child
    return None


def resolve_regression_reference(regressions_dir: Path, reference: str, language: str) -> Path | None:
    direct = regressions_dir / reference
    if direct.exists():
        return direct
    derived = regressions_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    # Prefix match: "reg-07" matches "reg-07-issue-with-spaces" (req-26 / chg-01, AC-04 一致)
    if regressions_dir.exists():
        for child in sorted(regressions_dir.iterdir()):
            if child.is_dir() and child.name.startswith(reference + "-"):
                return child
    return None


def append_change_to_requirement(requirement_dir: Path, change_id: str, title: str) -> None:
    change_map = requirement_dir / "changes.md"
    if not change_map.exists():
        return
    line = f"- [ ] `{change_id}`: {title}\n"
    text = change_map.read_text(encoding="utf-8")
    if line not in text:
        if text.rstrip().endswith("- None yet") or text.rstrip().endswith("- 暂无"):
            text = text.replace("- None yet", line.rstrip()).replace("- 暂无", line.rstrip())
        else:
            text = text.rstrip() + "\n" + line
        change_map.write_text(text.rstrip() + "\n", encoding="utf-8")




def _sync_requirement_workflow_managed_files(
    root: Path,
    *,
    include_agents: bool,
    include_claude: bool,
    check: bool,
    force_managed: bool,
) -> tuple[dict[str, str], list[str]]:
    config = ensure_config(root)
    language = config["language"]
    actions: list[str] = []
    for directory in _required_dirs(root):
        if check:
            if not directory.exists():
                actions.append(f"would create {directory.relative_to(root).as_posix()}/")
        else:
            directory.mkdir(parents=True, exist_ok=True)

    managed_contents = _managed_file_contents(root, language=language, include_agents=include_agents, include_claude=include_claude)
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    for relative, content in managed_contents.items():
        path = root / relative
        desired_hash = _managed_hash(content)
        if not path.exists():
            actions.append(f"{'missing' if check else 'created'} {relative}")
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue
        current = path.read_text(encoding="utf-8")
        current_hash = _managed_hash(current)
        if current == content:
            actions.append(f"current {relative}")
            refreshed_state[relative] = desired_hash
            continue
        if managed_state.get(relative) == current_hash or force_managed:
            label = "would update" if check else "updated"
            if force_managed and managed_state.get(relative) != current_hash:
                label = "would overwrite modified" if check else "overwrote modified"
            actions.append(f"{label} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue
        actions.append(f"skipped modified {relative}")

    if not check:
        save_requirement_runtime(root, load_requirement_runtime(root))
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))

    return config, actions


def _prune_empty_dirs(path: Path) -> None:
    if not path.exists() or not path.is_dir():
        return
    for child in sorted(path.iterdir()):
        if child.is_dir():
            _prune_empty_dirs(child)
    if not any(path.iterdir()):
        path.rmdir()


def _unique_backup_destination(root: Path, relative: Path) -> Path:
    base = root / LEGACY_CLEANUP_ROOT / relative
    if not base.exists():
        return base
    counter = 2
    while True:
        candidate = base.parent / f"{base.name}-{counter}"
        if not candidate.exists():
            return candidate
        counter += 1


def cleanup_legacy_workflow_artifacts(root: Path, check: bool) -> list[str]:
    actions: list[str] = []
    for relative in LEGACY_CLEANUP_TARGETS:
        path = root / relative
        if not path.exists():
            continue
        if path.is_dir() and not check:
            _prune_empty_dirs(path)
            if not path.exists():
                actions.append(f"removed empty legacy {relative.as_posix()}/")
                continue
        elif path.is_dir() and check:
            # Predictive empty-prune for check mode.
            has_payload = any(child for child in path.rglob("*") if child.is_file())
            if not has_payload:
                actions.append(f"would remove empty legacy {relative.as_posix()}/")
                continue

        if path.is_dir():
            backup_destination = _unique_backup_destination(root, relative)
            actions.append(
                f"{'would archive legacy' if check else 'archived legacy'} {relative.as_posix()} -> {backup_destination.relative_to(root).as_posix()}"
            )
            if not check:
                backup_destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(backup_destination))
        elif path.is_file():
            backup_destination = _unique_backup_destination(root, relative)
            actions.append(
                f"{'would archive legacy' if check else 'archived legacy'} {relative.as_posix()} -> {backup_destination.relative_to(root).as_posix()}"
            )
            if not check:
                backup_destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(path), str(backup_destination))
    for relative in OPTIONAL_EMPTY_DIRS:
        path = root / relative
        if not path.exists() or not path.is_dir():
            continue
        if check:
            has_payload = any(child for child in path.rglob("*") if child.is_file())
            if not has_payload:
                actions.append(f"would remove empty optional {relative.as_posix()}/")
            continue
        _prune_empty_dirs(path)
        if not path.exists():
            actions.append(f"removed empty optional {relative.as_posix()}/")
    return actions


def init_repo(root: Path, write_agents: bool, write_claude: bool) -> int:
    _, actions = _sync_requirement_workflow_managed_files(
        root,
        include_agents=write_agents,
        include_claude=write_claude,
        check=False,
        force_managed=False,
    )

    print("Created files:")
    for action in actions:
        if action.startswith("created "):
            print(f"- {root / action.removeprefix('created ')}")
    print("")
    print("Skipped existing files:")
    for action in actions:
        if action.startswith("current ") or action.startswith("skipped modified "):
            print(f"- {root / action.split(' ', 1)[1]}")
    return 0


def migrate_legacy_docs_to_workflow(root: Path) -> list[str]:
    """Migrate legacy docs/ workflow data to .workflow/ when upgrading from older harness versions."""
    old_root = root / "docs"
    new_root = root / ".workflow"
    markers = [
        old_root / "context" / "rules" / "workflow-runtime.yaml",
        old_root / "versions",
    ]
    if not any(m.exists() for m in markers):
        return []
    actions: list[str] = []
    for src in sorted(old_root.rglob("*")):
        if not src.is_file():
            continue
        relative = src.relative_to(old_root)
        dst = new_root / relative
        if dst.exists():
            actions.append(f"skipped (exists) .workflow/{relative}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        actions.append(f"migrated docs/{relative} → .workflow/{relative}")
    return actions


def _ensure_workflow_dir_gitignore(root: Path) -> None:
    """Ensure .workflow/ is not excluded by .gitignore."""
    gitignore = root / ".gitignore"
    marker = "!.workflow/"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if marker in content:
            return
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n# harness workflow directory (must not be ignored)\n{marker}\n"
        gitignore.write_text(content, encoding="utf-8")
    else:
        gitignore.write_text(
            f"# harness workflow directory (must not be ignored)\n{marker}\n",
            encoding="utf-8",
        )


def _migrate_workflow_dir(root: Path) -> bool:
    """Migrate .workflow/ → .workflow/ for backward compatibility. Returns True if migrated."""
    old_dir = root / "workflow"
    new_dir = root / ".workflow"
    if old_dir.exists() and not new_dir.exists():
        old_dir.rename(new_dir)
        print(f"Migrated {old_dir.name}/ → {new_dir.name}/")
        return True
    return False


def install_repo(root: Path, force_skill: bool = False) -> int:
    # Lazy import to avoid circular dependency
    from harness_workflow.cli import prompt_platform_selection

    _migrate_workflow_dir(root)
    _ensure_workflow_dir_gitignore(root)

    migration_actions = migrate_legacy_docs_to_workflow(root)
    if migration_actions:
        print("Migrated legacy docs/ → .workflow/:")
        for action in migration_actions:
            print(f"- {action}")
        print("")

    # Capture platform state before local skills are installed; otherwise the just-copied
    # qoder skill tree makes a brand-new repository look partially configured.
    active_platforms = get_active_platforms(str(root))
    active_list = [p for p, is_active in active_platforms.items() if is_active]

    skill_paths = install_local_skills(root, force=force_skill)
    print("Installed local skills:")
    for skill_path in skill_paths:
        print(f"- {skill_path}")

    # If no existing config, default to all platforms
    if not active_list:
        selected = ["codex", "qoder", "cc", "kimi"]
        print("\nNew installation: enabling all platforms (codex, qoder, cc, kimi)")
    else:
        # Interactive selection for re-install
        print(f"\nCurrent active platforms: {', '.join(active_list)}")
        selected = prompt_platform_selection(active_list)
        if not selected:
            selected = ["codex", "qoder", "cc", "kimi"]
            print("No selection made, using all platforms")

    # Sync platform state (backup/restore)
    result = sync_platforms_state(selected, str(root))
    if result.get("backed_up"):
        print(f"Backed up: {', '.join(result['backed_up'])}")
    if result.get("restored"):
        print(f"Restored from backup: {', '.join(result['restored'])}")
    if result.get("need_generate"):
        print(f"Generated new: {', '.join(result['need_generate'])}")
    if result.get("kept"):
        print(f"Kept: {', '.join(result['kept'])}")

    # Generate configs for selected platforms
    write_agents = "codex" in selected
    write_claude = "cc" in selected

    return init_repo(root, write_agents=write_agents, write_claude=write_claude)


def _migrate_state_files(root: Path) -> list[str]:
    """Migrate old state file formats to the latest schema."""
    actions: list[str] = []

    # Migrate runtime.yaml
    runtime_path = root / STATE_RUNTIME_PATH
    if runtime_path.exists():
        raw_runtime = load_simple_yaml(runtime_path)
        migrated = False
        if "ff_mode" not in raw_runtime:
            raw_runtime["ff_mode"] = False
            migrated = True
        if "ff_stage_history" not in raw_runtime:
            raw_runtime["ff_stage_history"] = []
            migrated = True
        if migrated:
            backup = runtime_path.with_suffix(runtime_path.suffix + ".bak")
            shutil.copy2(str(runtime_path), str(backup))
            save_requirement_runtime(root, raw_runtime)
            actions.append("migrated runtime.yaml to new format")

    # Migrate requirements/*.yaml
    req_state_dir = root / ".workflow" / "state" / "requirements"
    if req_state_dir.exists():
        for req_file in sorted(req_state_dir.rglob("*.yaml")):
            state = load_simple_yaml(req_file)
            if not state:
                continue
            migrated = False
            # Rename old fields
            if "req_id" in state:
                state["id"] = state.pop("req_id")
                migrated = True
            if "created" in state:
                state["created_at"] = state.pop("created")
                migrated = True
            if "completed" in state:
                state["completed_at"] = state.pop("completed")
                migrated = True
            # Add new fields
            if "started_at" not in state and "created_at" in state:
                state["started_at"] = str(state["created_at"])
                migrated = True
            if "stage_timestamps" not in state or isinstance(state.get("stage_timestamps"), str):
                state["stage_timestamps"] = {}
                migrated = True
            if migrated:
                backup = req_file.with_suffix(req_file.suffix + ".bak")
                shutil.copy2(str(req_file), str(backup))
                ordered = ["id", "title", "status", "created_at", "started_at", "completed_at", "archived_at", "stage_timestamps"]
                ordered += [k for k in state if k not in ordered]
                save_simple_yaml(req_file, state, ordered_keys=ordered)
                actions.append(f"migrated {req_file.name} to new format")

    return actions


def update_repo(root: Path, check: bool = False, force_managed: bool = False) -> int:
    actions: list[str] = []
    if not check:
        if _migrate_workflow_dir(root):
            actions.append("migrated .workflow/ → .workflow/")
        _ensure_workflow_dir_gitignore(root)
    migration_actions = migrate_legacy_docs_to_workflow(root) if not check else []
    if migration_actions:
        print("Migrated legacy docs/ → .workflow/:")
        for action in migration_actions:
            print(f"- {action}")
        print("")
    if check:
        actions.append("would refresh .codex/skills/harness")
        actions.append("would refresh .claude/skills/harness")
        actions.append("would refresh .qoder/skills/harness")
    else:
        install_local_skills(root, force=True)
        actions.append("refreshed .codex/skills/harness")
        actions.append("refreshed .claude/skills/harness")
        actions.append("refreshed .qoder/skills/harness")
    _, sync_actions = _sync_requirement_workflow_managed_files(
        root,
        include_agents=True,
        include_claude=True,
        check=check,
        force_managed=force_managed,
    )
    actions.extend(sync_actions)
    actions.extend(cleanup_legacy_workflow_artifacts(root, check))

    if not check:
        migrate_actions = _migrate_state_files(root)
        actions.extend(migrate_actions)

    _refresh_experience_index(root)

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    return 0


def set_language(root: Path, language: str) -> int:
    config = ensure_config(root)
    config["language"] = normalize_language(language)
    save_config(root, config)
    save_requirement_runtime(root, load_requirement_runtime(root))
    print(f"Language set to {config['language']}")
    print("Run `harness update` if you want managed templates and guides to refresh in the new language.")
    return 0


def _next_req_id(root: Path) -> str:
    """Return the next available req-NN id.

    扫描多个来源以避免 id 回滚：
      - ``.workflow/state/requirements``（runtime state 产出）
      - ``.workflow/flow/requirements``（legacy 路径）
      - ``resolve_requirement_root(root)``（当前 requirement 根，新/过渡路径）
    """
    max_num = 0
    scan_dirs = [
        root / ".workflow" / "state" / "requirements",
        root / ".workflow" / "flow" / "requirements",
        resolve_requirement_root(root),
    ]
    seen: set[Path] = set()
    for d in scan_dirs:
        try:
            key = d.resolve()
        except OSError:
            key = d
        if key in seen:
            continue
        seen.add(key)
        if not d.exists():
            continue
        for item in d.iterdir():
            m = re.match(r"req-(\d+)", item.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"req-{max_num + 1:02d}"


def _next_bugfix_id(root: Path) -> str:
    """Return the next available bugfix-N id."""
    max_num = 0
    for d in [
        root / "artifacts" / "bugfixes",
        root / ".workflow" / "state" / "bugfixes",
        root / ".workflow" / "flow" / "bugfixes",
    ]:
        if not d.exists():
            continue
        for item in d.iterdir():
            m = re.match(r"bugfix-(\d+)", item.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"bugfix-{max_num + 1}"


def _next_suggestion_id(root: Path) -> str:
    """计算下一个 sug-NN 编号（req-28 / chg-01，覆盖 AC-15）。

    同时扫描 `.workflow/flow/suggestions/` 当前目录与 `archive/` 子目录，
    聚合两处的最大编号后 +1，保证当前目录被清空后编号不会回滚到 01
    与 `archive/` 下历史 sug 冲突。
    """
    pattern = re.compile(r"^sug-(\d+)(?:-|\.)")
    max_num = 0
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    scan_dirs = [suggestions_dir, suggestions_dir / "archive"]
    for dir_path in scan_dirs:
        if not dir_path.exists():
            continue
        for p in dir_path.glob("sug-*.md"):
            m = pattern.match(p.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"sug-{max_num + 1:02d}"


def _next_regression_id(regressions_base: Path) -> str:
    """Return the next available `reg-NN` id under a regressions base directory.

    约定（req-26 / chg-01，覆盖 AC-04）：regression 产出目录必须以 `reg-{N:02d}-`
    前缀开头，N 取 `regressions_base` 下已有 `reg-\\d+-...` 目录的最大值 +1。
    若 base 尚不存在，直接从 1 开始。
    """
    max_num = 0
    if regressions_base.exists():
        for item in regressions_base.iterdir():
            if not item.is_dir():
                continue
            m = re.match(r"reg-(\d+)", item.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"reg-{max_num + 1:02d}"


def extract_suggestions_from_done_report(root: Path, req_id: str) -> list[str]:
    """Extract improvement suggestions from done-report.md and create suggestion files."""
    done_report = root / ".workflow" / "state" / "sessions" / req_id / "done-report.md"
    if not done_report.exists():
        return []

    text = done_report.read_text(encoding="utf-8")
    # Find the "## 改进建议" section
    match = re.search(r"##\s*改进建议\s*\n(.*?)(?=\n##\s|$)", text, re.DOTALL)
    if not match:
        # Also try English variant
        match = re.search(r"##\s*Improvement Suggestions\s*\n(.*?)(?=\n##\s|$)", text, re.DOTALL)
    if not match:
        return []

    section = match.group(1)
    suggestions: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue
        # Match blockquotes like "> **建议 1**：xxx" or "> 建议：xxx"
        if stripped.startswith(">"):
            content = stripped[1:].strip()
            # Remove bold markers like **建议 1**：
            content = re.sub(r"\*\*[^*]+\*\*\s*[：:]\s*", "", content)
            if content and len(content) >= 5:
                suggestions.append(content)
            continue
        # Match list items
        if re.match(r"^[-*\d]\.?\s+", stripped):
            content = re.sub(r"^[-*\d]\.?\s+", "", stripped)
            if content and len(content) >= 5:
                suggestions.append(content)
            continue

    created: list[str] = []
    for suggestion in suggestions:
        try:
            create_suggestion(root, suggestion)
            created.append(suggestion[:40])
        except SystemExit:
            pass

    if created:
        print(f"Created {len(created)} suggestion(s) from done report.")
    return created


def create_suggestion(root: Path, content: str, title: str | None = None) -> int:
    ensure_harness_root(root)
    suggestion_content = content.strip()
    if not suggestion_content:
        raise SystemExit("Suggestion content is required.")

    suggest_id = _next_suggestion_id(root)
    slug = slugify(title or suggestion_content) or "suggestion"
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    suggestions_dir.mkdir(parents=True, exist_ok=True)
    suggest_path = suggestions_dir / f"{suggest_id}-{slug}.md"

    frontmatter = f"---\nid: {suggest_id}\ncreated_at: {json.dumps(date.today().isoformat(), ensure_ascii=False)}\nstatus: pending\n---\n\n{suggestion_content}\n"
    suggest_path.write_text(frontmatter, encoding="utf-8")

    print(f"Created suggestion: {suggest_path.relative_to(root)}")
    return 0


def list_suggestions(root: Path) -> int:
    ensure_harness_root(root)
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    if not suggestions_dir.exists():
        print("No suggestions found.")
        return 0

    files = sorted(suggestions_dir.glob("sug-*.md"))
    if not files:
        print("No suggestions found.")
        return 0

    print("Suggestions:")
    for path in files:
        state = load_simple_yaml(path)
        sid = str(state.get("id", path.stem)).strip()
        created = str(state.get("created_at", "")).strip()
        status = str(state.get("status", "pending")).strip()
        body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip().replace("\n", " ")
        summary = body[:60] + "..." if len(body) > 60 else body
        print(f"  {sid} [{status}] ({created}) {summary}")
    return 0


def apply_suggestion(root: Path, suggest_id: str) -> int:
    ensure_harness_root(root)
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    if not suggestions_dir.exists():
        raise SystemExit("No suggestions found.")

    # req-28 / chg-01（AC-15）：frontmatter `id:` 优先匹配，失败时回退 filename。
    # 兼容三种形态：(a) frontmatter.id 精确等于；(b) path.stem 精确等于（如 `sug-01`）；
    # (c) path.stem 以 `sug-NN-` 开头。
    target = None
    for path in sorted(suggestions_dir.glob("sug-*.md")):
        state = load_simple_yaml(path)
        sid_from_yaml = str(state.get("id", "")).strip()
        sid_from_filename = path.stem
        if (
            sid_from_yaml == suggest_id
            or sid_from_filename == suggest_id
            or sid_from_filename.startswith(suggest_id + "-")
        ):
            target = path
            break

    if not target:
        raise SystemExit(f"Suggestion not found: {suggest_id}")

    state = load_simple_yaml(target)
    body = target.read_text(encoding="utf-8").split("---", 2)[-1].strip()
    # bugfix-3：截断首行到 60 字符作为 title 候选（slug 清洗仍下沉给 create_requirement
    # 执行，这里只保证 create_requirement 拿到的 raw title 不会过长撑爆路径）。
    first_line = body.splitlines()[0].strip() if body else ""
    title = first_line[:60].strip() or suggest_id

    result = create_requirement(root, title)
    if result == 0:
        # bugfix-3：成功后将源 sug 文件 move 到 archive/ 并翻转 frontmatter status。
        archive_dir = suggestions_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / target.name
        target.replace(archive_path)
        text = archive_path.read_text(encoding="utf-8")
        updated = text.replace("status: pending", "status: applied")
        archive_path.write_text(updated, encoding="utf-8")
        print(f"Applied suggestion {suggest_id} to requirement.")
    return result


def delete_suggestion(root: Path, suggest_id: str) -> int:
    ensure_harness_root(root)
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    if not suggestions_dir.exists():
        raise SystemExit("No suggestions found.")

    # req-28 / chg-01（AC-15）：frontmatter `id:` 优先匹配，失败时回退 filename。
    target = None
    for path in sorted(suggestions_dir.glob("sug-*.md")):
        state = load_simple_yaml(path)
        sid_from_yaml = str(state.get("id", "")).strip()
        sid_from_filename = path.stem
        if (
            sid_from_yaml == suggest_id
            or sid_from_filename == suggest_id
            or sid_from_filename.startswith(suggest_id + "-")
        ):
            target = path
            break

    if not target:
        raise SystemExit(f"Suggestion not found: {suggest_id}")

    target.unlink()
    print(f"Deleted suggestion: {suggest_id}")
    return 0


def archive_suggestion(root: Path, suggest_id: str) -> int:
    ensure_harness_root(root)
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    if not suggestions_dir.exists():
        raise SystemExit("No suggestions found.")

    # req-28 / chg-01（AC-15）：frontmatter `id:` 优先匹配，失败时回退 filename，
    # 同时兼容 `sug-NN` 与 `sug-NN-slug` 两种 stem 形态。
    target = None
    for path in sorted(suggestions_dir.glob("sug-*.md")):
        state = load_simple_yaml(path)
        sid_from_yaml = str(state.get("id", "")).strip()
        sid_from_filename = path.stem
        if (
            sid_from_yaml == suggest_id
            or sid_from_filename == suggest_id
            or sid_from_filename.startswith(suggest_id + "-")
        ):
            target = path
            break

    if not target:
        raise SystemExit(f"Suggestion not found: {suggest_id}")

    text = target.read_text(encoding="utf-8")
    # Check if already archived
    if "status: archived" in text or "已归档" in text:
        raise SystemExit(f"Suggestion {suggest_id} is already archived.")

    # Check if applied (supports both YAML frontmatter and Markdown format)
    is_applied = False
    if "status: applied" in text:
        is_applied = True
    elif "已应用 (applied)" in text or "> **状态**: 已应用" in text:
        is_applied = True

    if not is_applied:
        raise SystemExit(f"Suggestion {suggest_id} is not in 'applied' status. Only applied suggestions can be archived.")

    today = date.today().isoformat()

    # Replace status marker (supports both formats)
    if "> **状态**: 已应用 (applied)" in text:
        updated = text.replace("> **状态**: 已应用 (applied)", f"> **状态**: 已归档 (archived)\n> **归档时间**: {today}")
    elif "> **状态**: applied" in text:
        updated = text.replace("> **状态**: applied", f"> **状态**: archived\n> **归档时间**: {today}")
    elif "status: applied" in text:
        updated = text.replace("status: applied", f"status: archived\narchived_at: {today}")
    else:
        updated = text

    archive_dir = suggestions_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / target.name
    target.rename(archive_path)
    archive_path.write_text(updated, encoding="utf-8")

    print(f"Archived suggestion: {suggest_id} -> {archive_path.relative_to(root)}")
    return 0


def apply_all_suggestions(root: Path, pack_title: str = "") -> int:
    # 本函数强制将所有 pending suggest 打包为单一需求
    ensure_harness_root(root)
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    if not suggestions_dir.exists():
        print("No suggestions found.")
        return 0

    pending: list[tuple[Path, str, str]] = []
    for path in sorted(suggestions_dir.glob("sug-*.md")):
        state = load_simple_yaml(path)
        if str(state.get("status", "pending")).strip() != "pending":
            continue
        body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        title = body.splitlines()[0].strip() if body else str(state.get("id", path.stem)).strip()
        suggest_id = str(state.get("id", path.stem)).strip()
        pending.append((path, suggest_id, title))

    if not pending:
        print("No pending suggestions found.")
        return 0

    title = pack_title.strip()
    if not title:
        title = f"批量建议合集（{len(pending)}条）"

    # 强制只创建 1 个需求，无论 pending 数量多少
    result = create_requirement(root, title)
    if result != 0:
        print(f"Failed to create requirement from {len(pending)} suggestion(s).")
        return 1

    req_id = str(load_requirement_runtime(root).get("current_requirement", "")).strip()

    # 向生成的 requirement.md 追加被合并的 suggest 清单
    if req_id:
        req_dir = resolve_requirement_root(root) / f"{req_id}-{title}"
        req_md = req_dir / "requirement.md"
        if req_md.exists():
            lines = ["\n## 合并建议清单\n"]
            for _, suggest_id, suggest_title in pending:
                lines.append(f"- {suggest_id}: {suggest_title}")
            lines.append("")
            req_md.write_text(req_md.read_text(encoding="utf-8") + "\n".join(lines), encoding="utf-8")

    deleted: list[str] = []
    failed_delete: list[str] = []
    for path, suggest_id, _ in pending:
        try:
            path.unlink()
            deleted.append(suggest_id)
        except OSError:
            failed_delete.append(suggest_id)

    print(f"Packed {len(deleted)} suggestion(s) into {req_id}:")
    for sid in deleted:
        print(f"  - {sid}")
    if failed_delete:
        print(f"Failed to delete {len(failed_delete)} suggestion file(s):")
        for sid in failed_delete:
            print(f"  - {sid}")

    return 0 if not failed_delete else 1


def create_requirement(root: Path, name: str | None, requirement_id: str | None = None, title: str | None = None) -> int:
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    repo_name = root.name
    requirement_title = (name or title or "").strip()
    if not requirement_title:
        raise SystemExit("A requirement title is required.")

    req_num_id = requirement_id.strip() if requirement_id else _next_req_id(root)
    # bugfix-3：title 经 slugify + 长度上限清洗后再拼 dir_name，避免 `/` 被 Path
    # 拆成多级嵌套或超长 title 撑破文件系统。state yaml 的 title 字段保留原文。
    slug_part = _path_slug(requirement_title)
    dir_name = f"{req_num_id}-{slug_part}" if slug_part else req_num_id
    branch = _get_git_branch(root) or "main"
    requirement_dir = root / "artifacts" / branch / "requirements" / dir_name
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": req_num_id, "TITLE": requirement_title}

    write_if_missing(
        requirement_dir / "requirement.md",
        render_template("requirement.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    (requirement_dir / "changes").mkdir(parents=True, exist_ok=True)

    state_file = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
    if not state_file.exists():
        today = date.today().isoformat()
        save_simple_yaml(
            state_file,
            {
                "id": req_num_id,
                "title": requirement_title,
                "stage": "requirement_review",
                "status": "active",
                "created_at": today,
                "started_at": today,
                "completed_at": "",
                "stage_timestamps": {},
                "description": "",
            },
            ordered_keys=["id", "title", "stage", "status", "created_at", "started_at", "completed_at", "stage_timestamps", "description"],
        )
        created.append(str(state_file.relative_to(root)))

    active_reqs = list(runtime.get("active_requirements", []))
    if req_num_id not in [str(r) for r in active_reqs]:
        active_reqs.append(req_num_id)
    runtime["operation_type"] = "requirement"
    runtime["operation_target"] = req_num_id
    runtime["current_requirement"] = req_num_id
    runtime["stage"] = "requirement_review"
    runtime["active_requirements"] = active_reqs
    save_requirement_runtime(root, runtime)

    print(f"Requirement workspace: {requirement_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_bugfix(root: Path, name: str | None, bugfix_id: str | None = None, title: str | None = None) -> int:
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    repo_name = root.name
    bugfix_title = (name or title or "").strip()
    if not bugfix_title:
        raise SystemExit("A bugfix title is required.")

    bfx_num_id = bugfix_id.strip() if bugfix_id else _next_bugfix_id(root)
    # bugfix-3：与 create_requirement 同源的 slug 清洗 + 长度截断。
    slug_part = _path_slug(bugfix_title)
    dir_name = f"{bfx_num_id}-{slug_part}" if slug_part else bfx_num_id
    branch = _get_git_branch(root) or "main"
    bugfix_dir = root / "artifacts" / branch / "bugfixes" / dir_name
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": bfx_num_id, "TITLE": bugfix_title}

    write_if_missing(
        bugfix_dir / "bugfix.md",
        render_template("bugfix.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    write_if_missing(
        bugfix_dir / "session-memory.md",
        render_template("session-memory.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    write_if_missing(
        bugfix_dir / "regression" / "diagnosis.md",
        render_template("diagnosis.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    write_if_missing(
        bugfix_dir / "regression" / "required-inputs.md",
        render_template("regression-required-inputs.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    write_if_missing(
        bugfix_dir / "test-evidence.md",
        render_template("self-test.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )

    state_file = root / ".workflow" / "state" / "bugfixes" / f"{dir_name}.yaml"
    if not state_file.exists():
        today = date.today().isoformat()
        save_simple_yaml(
            state_file,
            {
                "id": bfx_num_id,
                "title": bugfix_title,
                "stage": "regression",
                "status": "active",
                "created_at": today,
                "started_at": today,
                "completed_at": "",
                "stage_timestamps": {},
                "description": "",
            },
            ordered_keys=["id", "title", "stage", "status", "created_at", "started_at", "completed_at", "stage_timestamps", "description"],
        )
        created.append(str(state_file.relative_to(root)))

    active_reqs = list(runtime.get("active_requirements", []))
    if bfx_num_id not in [str(r) for r in active_reqs]:
        active_reqs.append(bfx_num_id)
    runtime["operation_type"] = "bugfix"
    runtime["operation_target"] = bfx_num_id
    runtime["current_requirement"] = bfx_num_id  # 兼容字段
    runtime["stage"] = "regression"
    runtime["active_requirements"] = active_reqs
    save_requirement_runtime(root, runtime)

    print(f"Bugfix workspace: {bugfix_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def _next_chg_id(req_dir: Path) -> str:
    """Return the next available chg-NN id within a requirement."""
    max_num = 0
    changes_dir = req_dir / "changes"
    if changes_dir.exists():
        for item in changes_dir.iterdir():
            m = re.match(r"chg-(\d+)", item.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"chg-{max_num + 1:02d}"


def create_change(
    root: Path,
    name: str | None,
    change_id: str | None = None,
    title: str | None = None,
    requirement_id: str = "",
) -> int:
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    repo_name = root.name
    change_title = (name or title or "").strip()
    if not change_title:
        raise SystemExit("A change title is required.")

    req_ref = requirement_id.strip() or str(runtime.get("current_requirement", "")).strip()
    req_dir = None
    if req_ref:
        branch = _get_git_branch(root) or "main"
        req_dir = resolve_requirement_reference(
            root / "artifacts" / branch / "requirements", req_ref, config["language"]
        )
    if not req_dir:
        raise SystemExit("No active requirement. Run `harness requirement <title>` first.")

    chg_num_id = change_id.strip() if change_id else _next_chg_id(req_dir)
    # req-26 / chg-02（合并 B）：`harness change` 生成的目录名必须走统一
    # slugify 清洗，与 regression 命令簇（chg-01）共用 `slugify_preserve_unicode`。
    # 保留 `chg-NN-` 前缀，空格 / 中文冒号等标点一律折叠为 `-`，保持 CJK。
    slug_part = slugify_preserve_unicode(change_title) or "change"
    dir_name = f"{chg_num_id}-{slug_part}"
    change_dir = req_dir / "changes" / dir_name
    created: list[str] = []
    skipped: list[str] = []
    linked_requirement = req_ref
    replacements = {"ID": chg_num_id, "TITLE": change_title, "REQUIREMENT_ID": linked_requirement or "None"}

    write_if_missing(change_dir / "change.md", render_template("change.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "regression" / "required-inputs.md", render_template("regression-required-inputs.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_regression(root: Path, name: str | None, regression_id: str | None = None, title: str | None = None) -> int:
    """Create a regression workspace.

    命名约定（req-26 / chg-01，覆盖 AC-04）：
    - 产出目录名统一形如 ``{reg-NN}-{slug(title)}``；其中：
        * ``reg-NN`` 由 ``_next_regression_id`` 在当前 ``regressions_base`` 下分配；
        * ``slug(title)`` 使用 ``slugify_preserve_unicode`` —— 英文 kebab-case、
          中文等非 ASCII 字母保留，空格 / 标点 / 非法路径字符折叠为 ``-``。
    - ``runtime["current_regression"]`` 仅写 ``reg-NN``（纯 id，便于 ``--confirm`` /
      ``--testing`` 等后续动作引用），目录解析走 ``resolve_regression_reference``
      的前缀匹配。
    """
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    repo_name = root.name
    regression_title, _legacy_resolved_id = resolve_title_and_id(name, regression_id, title, config["language"])

    req_ref = str(runtime.get("current_requirement", "")).strip()
    req_dir = None
    if req_ref:
        req_dir = resolve_requirement_reference(
            resolve_requirement_root(root), req_ref, config["language"]
        )
    regressions_base = (req_dir / "regressions") if req_dir else (resolve_requirement_root(root).parent / "regressions")

    # 分配 reg-NN 前缀（若调用方显式传入 regression_id 且已是 reg-\d+ 形式则沿用，否则按顺序分配）
    if regression_id and re.match(r"^reg-\d+$", regression_id.strip()):
        reg_num_id = regression_id.strip()
    else:
        reg_num_id = _next_regression_id(regressions_base)

    slug_part = slugify_preserve_unicode(regression_title) or "regression"
    dir_name = f"{reg_num_id}-{slug_part}"
    regression_dir = regressions_base / dir_name
    created: list[str] = []
    skipped: list[str] = []
    # 模板里的 {{ID}} 统一填充为纯 reg-NN（与 runtime.current_regression 一致，
    # 便于后续命令通过 id 反查目录）。
    replacements = {"ID": reg_num_id, "TITLE": regression_title}

    write_if_missing(regression_dir / "regression.md", render_template("regression.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "analysis.md", render_template("regression-analysis.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "decision.md", render_template("regression-decision.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "meta.yaml", render_template("regression-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    runtime["current_regression"] = reg_num_id
    save_requirement_runtime(root, runtime)
    record_feedback_event(root, "regression_created", {"regression_id": reg_num_id, "dir_name": dir_name})

    print(f"Regression workspace: {regression_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def _ensure_regression_experience(root: Path, regression_id: str) -> None:
    exp_dir = root / ".workflow" / "context" / "experience" / "regression"
    exp_file = exp_dir / f"{regression_id}.md"
    if exp_file.exists():
        return
    exp_dir.mkdir(parents=True, exist_ok=True)
    content = f"""# Regression Experience: {regression_id}

## Date
{datetime.now(timezone.utc).isoformat()}

## Phenomenon
<!-- Describe the regression symptom -->

## Root Cause
<!-- Why did this happen? -->

## Improvement
<!-- What process or code changes can prevent this? -->
"""
    exp_file.write_text(content, encoding="utf-8")
    print(f"Created regression experience: {exp_file.relative_to(root)}")


def _refresh_experience_index(root: Path) -> None:
    """Auto-generate `.workflow/context/experience/index.md` from existing experience files."""
    exp_root = root / ".workflow" / "context" / "experience"
    index_file = exp_root / "index.md"
    if not exp_root.exists():
        return

    entries: dict[str, list[tuple[str, str]]] = {}
    for md_file in sorted(exp_root.rglob("*.md")):
        rel = md_file.relative_to(exp_root).as_posix()
        if rel == "index.md":
            continue
        category = rel.split("/")[0] if "/" in rel else "general"
        title_line = md_file.read_text(encoding="utf-8").splitlines()[0] if md_file.stat().st_size > 0 else ""
        title = title_line.lstrip("# ").strip() or rel
        entries.setdefault(category, []).append((rel, title))

    lines = ["# Experience Index", "", f"> Auto-generated index of `{exp_root.relative_to(root)}`.", ""]
    for category in sorted(entries.keys()):
        lines.append(f"## {category}")
        for rel, title in sorted(entries[category]):
            lines.append(f"- [{rel}]({rel}) — {title}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Update this index by running `harness update`.")
    lines.append("")

    content = "\n".join(lines)
    if not index_file.exists() or index_file.read_text(encoding="utf-8") != content:
        index_file.write_text(content, encoding="utf-8")
        print(f"Refreshed experience index: {index_file.relative_to(root)}")


def _locate_regression_dir(root: Path, regression_id: str, language: str) -> Path | None:
    """根据 regression id 在当前仓库定位产出目录。

    查找优先级：
    1. ``artifacts/{branch}/requirements/{current_requirement}/regressions/`（若 runtime
       有 current_requirement）；
    2. ``artifacts/{branch}/regressions/``（无 requirement 时的兜底）；
    3. ``.workflow/flow/regressions/``（legacy 路径）。
    """
    runtime = load_requirement_runtime(root)
    candidates: list[Path] = []
    req_ref = str(runtime.get("current_requirement", "")).strip()
    if req_ref:
        req_dir = resolve_requirement_reference(resolve_requirement_root(root), req_ref, language)
        if req_dir is not None:
            candidates.append(req_dir / "regressions")
    candidates.append(resolve_requirement_root(root).parent / "regressions")
    candidates.append(root / ".workflow" / "flow" / "regressions")
    for base in candidates:
        found = resolve_regression_reference(base, regression_id, language)
        if found is not None:
            return found
    return None


def _update_regression_meta_status(root: Path, regression_id: str, status: str) -> None:
    """更新 regression 产出目录下 ``meta.yaml`` 的 ``status`` 字段（若目录存在）。

    对 ``--confirm`` 语义友好：即使找不到 meta.yaml 也静默跳过，不影响主流程。
    """
    try:
        config = ensure_config(root)
    except SystemExit:
        return
    reg_dir = _locate_regression_dir(root, regression_id, config["language"])
    if reg_dir is None:
        return
    meta_path = reg_dir / "meta.yaml"
    if not meta_path.exists():
        return
    meta = load_item_meta(meta_path)
    meta["status"] = status
    save_item_meta(meta_path, meta)


def regression_action(
    root: Path,
    *,
    status_only: bool = False,
    confirm: bool = False,
    reject: bool = False,
    cancel: bool = False,
    change_title: str = "",
    requirement_title: str = "",
    to_testing: bool = False,
) -> int:
    runtime = load_requirement_runtime(root)
    regression_id = str(runtime.get("current_regression", "")).strip()
    if not regression_id:
        raise SystemExit("No active regression. Start one with `harness regression \"<issue>\"` first.")

    if status_only:
        print(f"current_regression: {regression_id}")
        return 0

    chosen = sum(bool(value) for value in [confirm, reject, cancel, to_testing, bool(change_title), bool(requirement_title)])
    if chosen != 1:
        raise SystemExit("Choose exactly one regression action: --confirm, --reject, --cancel, --testing, --change, or --requirement.")

    if cancel or reject:
        _ensure_regression_experience(root, regression_id)
        runtime["current_regression"] = ""
        save_requirement_runtime(root, runtime)
        print(f"Regression {regression_id} {'cancelled' if cancel else 'rejected'}.")
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return 0

    if confirm:
        # req-26 / chg-01 / AC-01：--confirm 只做"确认问题真实"这一动作，
        # 不得清空 runtime.current_regression，也不得删除 regression 产出目录；
        # 后续 --testing / --change / --requirement 仍能继续消费该 regression。
        _ensure_regression_experience(root, regression_id)
        _update_regression_meta_status(root, regression_id, "confirmed")
        # 注意：不修改 runtime["current_regression"]。
        save_requirement_runtime(root, runtime)
        print(f"Regression {regression_id} confirmed. State preserved for subsequent --testing / --change / --requirement.")
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return 0

    if change_title:
        _ensure_regression_experience(root, regression_id)
        runtime["current_regression"] = ""
        save_requirement_runtime(root, runtime)
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return create_change(root, change_title)

    if requirement_title:
        _ensure_regression_experience(root, regression_id)
        runtime["current_regression"] = ""
        save_requirement_runtime(root, runtime)
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return create_requirement(root, requirement_title)

    if to_testing:
        _ensure_regression_experience(root, regression_id)
        _update_regression_meta_status(root, regression_id, "testing")
        runtime["current_regression"] = ""
        runtime["stage"] = "testing"
        save_requirement_runtime(root, runtime)
        print(f"Regression {regression_id} confirmed as bug. Stage rolled back to testing.")
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return 0

    return 0


def _extract_id_prefix(dir_name: str, pattern: str) -> str:
    """从目录名中抽取 `{id}-` 前缀（如 `req-26-uav-split` → `req-26`）。

    pattern 形如 ``r"^(req-\\d+)"`` / ``r"^(chg-\\d+)"`` / ``r"^(bugfix-\\d+)"``。
    未匹配时返回空串，由调用方兜底。
    """
    match = re.match(pattern, dir_name)
    return match.group(1) if match else ""


def _state_yaml_for_requirement(root: Path, dir_basename: str) -> Path | None:
    """查找 `.workflow/state/requirements/` 下与某 requirement 目录名同名的 yaml。

    先尝试直接 `{dir_basename}.yaml`；若不存在，则按 `{id}-` 前缀前缀匹配
    第一个命中文件（兼容历史上 state yaml 文件名与产出目录名不完全一致
    的场景）。
    """
    state_dir = root / ".workflow" / "state" / "requirements"
    if not state_dir.exists():
        return None
    direct = state_dir / f"{dir_basename}.yaml"
    if direct.exists():
        return direct
    id_prefix = _extract_id_prefix(dir_basename, r"^(req-\d+)")
    if id_prefix:
        for child in sorted(state_dir.iterdir()):
            if child.is_file() and child.suffix == ".yaml" and child.stem.startswith(id_prefix + "-"):
                return child
    return None


def _state_yaml_for_bugfix(root: Path, dir_basename: str) -> Path | None:
    """查找 `.workflow/state/bugfixes/` 下与某 bugfix 目录同名的 yaml。"""
    state_dir = root / ".workflow" / "state" / "bugfixes"
    if not state_dir.exists():
        return None
    direct = state_dir / f"{dir_basename}.yaml"
    if direct.exists():
        return direct
    id_prefix = _extract_id_prefix(dir_basename, r"^(bugfix-\d+)")
    if id_prefix:
        for child in sorted(state_dir.iterdir()):
            if child.is_file() and child.suffix == ".yaml" and child.stem.startswith(id_prefix + "-"):
                return child
    return None


def rename_requirement(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    """Rename a requirement, preserving the `{id}-` prefix and syncing state yaml.

    req-26 / chg-02（AC-02）：
    - 目标目录名形如 ``{old_id}-{slug(new_title)}``，`{id}` 不得改变；
    - ``.workflow/state/requirements/{id}-{slug}.yaml`` 同步改名并更新 ``title`` 字段；
    - ``.workflow/state/runtime.yaml`` 的 ``current_requirement`` / ``active_requirements``
      存的是 id，本操作不改 id，因此保持原值——但为了一致性（防止潜在脏字段），
      统一走一次 ``save_requirement_runtime`` 重写。
    """
    config = ensure_config(root)
    requirements_dir = resolve_requirement_root(root)
    requirement_dir = resolve_requirement_reference(requirements_dir, current_name, config["language"])
    if not requirement_dir:
        raise SystemExit(f"Requirement does not exist: {current_name}")

    old_dir_name = requirement_dir.name
    meta_path = requirement_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path) if meta_path.exists() else {}
    # 解析 old_id：优先 meta.yaml，其次目录名前缀。
    old_id = item_meta.get("id", "") or _extract_id_prefix(old_dir_name, r"^(req-\d+)")
    if not old_id:
        # 兜底：若目录名完全不符合 `req-N[-...]` 模式，则直接用目录名作为 id。
        old_id = old_dir_name
    old_title = item_meta.get("title", old_id) or old_id

    new_title = (new_name or "").strip()
    if not new_title:
        raise SystemExit("A new requirement title is required.")
    new_slug = slugify_preserve_unicode(new_title) or new_title
    new_dir_name = f"{old_id}-{new_slug}"
    target_dir = requirements_dir / new_dir_name
    if target_dir.exists() and target_dir != requirement_dir:
        raise SystemExit(f"Target requirement already exists: {new_dir_name}")

    # 1) 目录重命名（保持 id 前缀不变）。
    if target_dir != requirement_dir:
        shutil.move(str(requirement_dir), str(target_dir))

    # 2) meta.yaml：id 保持不变，仅更新 title。
    new_meta_path = target_dir / "meta.yaml"
    if new_meta_path.exists():
        item_meta["id"] = old_id
        item_meta["title"] = new_title
        save_item_meta(new_meta_path, item_meta)
    replace_in_file(target_dir / "requirement.md", {old_title: new_title})

    # 3) 同步 state yaml：文件名改为 `{id}-{new_slug}.yaml`；更新内部 title 字段。
    old_state_path = _state_yaml_for_requirement(root, old_dir_name)
    new_state_path = root / ".workflow" / "state" / "requirements" / f"{new_dir_name}.yaml"
    if old_state_path is not None and old_state_path.exists():
        payload = load_simple_yaml(old_state_path)
        if not isinstance(payload, dict):
            payload = {}
        # 保留原有字段顺序（id/title/stage/status/...）
        payload["id"] = old_id
        payload["title"] = new_title
        new_state_path.parent.mkdir(parents=True, exist_ok=True)
        save_simple_yaml(
            new_state_path,
            payload,
            ordered_keys=["id", "title", "stage", "status", "created_at", "started_at", "completed_at", "stage_timestamps", "description"],
        )
        if old_state_path != new_state_path:
            try:
                old_state_path.unlink()
            except OSError:
                pass

    # 4) 同步 runtime.yaml：id 不变，仅作一次重写以保证持久化一致性。
    runtime = load_requirement_runtime(root)
    save_requirement_runtime(root, runtime)

    print(f"Requirement renamed: {old_dir_name} -> {new_dir_name}")
    return 0


def rename_change(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    """Rename a change, preserving the `{chg-NN}-` prefix.

    req-26 / chg-02（AC-02）：保持 ``chg-NN`` id 不变；标题走
    ``slugify_preserve_unicode``；不动 state yaml（change 无独立 state yaml）。
    """
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    req_ref = str(runtime.get("current_requirement", "")).strip()
    req_dir = None
    if req_ref:
        req_dir = resolve_requirement_reference(
            resolve_requirement_root(root), req_ref, config["language"]
        )
    if not req_dir:
        raise SystemExit("No active requirement. Cannot rename change without a current requirement.")

    changes_dir = req_dir / "changes"
    change_dir = resolve_requirement_reference(changes_dir, current_name, config["language"])
    if not change_dir:
        raise SystemExit(f"Change does not exist: {current_name}")

    old_dir_name = change_dir.name
    meta_path = change_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path) if meta_path.exists() else {}
    old_id = item_meta.get("id", "") or _extract_id_prefix(old_dir_name, r"^(chg-\d+)")
    if not old_id:
        old_id = old_dir_name
    old_title = item_meta.get("title", old_id) or old_id

    new_title = (new_name or "").strip()
    if not new_title:
        raise SystemExit("A new change title is required.")
    new_slug = slugify_preserve_unicode(new_title) or new_title
    new_dir_name = f"{old_id}-{new_slug}"
    target_dir = changes_dir / new_dir_name
    if target_dir.exists() and target_dir != change_dir:
        raise SystemExit(f"Target change already exists: {new_dir_name}")

    if target_dir != change_dir:
        shutil.move(str(change_dir), str(target_dir))
    new_meta_path = target_dir / "meta.yaml"
    if new_meta_path.exists():
        item_meta["id"] = old_id
        item_meta["title"] = new_title
        save_item_meta(new_meta_path, item_meta)
    replace_in_file(target_dir / "change.md", {old_title: new_title})

    print(f"Change renamed: {old_dir_name} -> {new_dir_name}")
    return 0


def rename_bugfix(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    """Rename a bugfix, preserving the `{bugfix-N}-` prefix and syncing state yaml.

    req-26 / chg-02（AC-02 延伸）：与 rename_requirement 对称。
    """
    config = ensure_config(root)
    branch = _get_git_branch(root) or "main"
    bugfix_root = root / "artifacts" / branch / "bugfixes"
    if not bugfix_root.exists():
        bugfix_root = root / "artifacts" / "bugfixes"
    bugfix_dir = resolve_requirement_reference(bugfix_root, current_name, config["language"])
    if not bugfix_dir:
        raise SystemExit(f"Bugfix does not exist: {current_name}")

    old_dir_name = bugfix_dir.name
    meta_path = bugfix_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path) if meta_path.exists() else {}
    old_id = item_meta.get("id", "") or _extract_id_prefix(old_dir_name, r"^(bugfix-\d+)")
    if not old_id:
        old_id = old_dir_name
    old_title = item_meta.get("title", old_id) or old_id

    new_title = (new_name or "").strip()
    if not new_title:
        raise SystemExit("A new bugfix title is required.")
    new_slug = slugify_preserve_unicode(new_title) or new_title
    new_dir_name = f"{old_id}-{new_slug}"
    target_dir = bugfix_root / new_dir_name
    if target_dir.exists() and target_dir != bugfix_dir:
        raise SystemExit(f"Target bugfix already exists: {new_dir_name}")

    if target_dir != bugfix_dir:
        shutil.move(str(bugfix_dir), str(target_dir))
    new_meta_path = target_dir / "meta.yaml"
    if new_meta_path.exists():
        item_meta["id"] = old_id
        item_meta["title"] = new_title
        save_item_meta(new_meta_path, item_meta)
    replace_in_file(target_dir / "bugfix.md", {old_title: new_title})

    # 同步 state yaml
    old_state_path = _state_yaml_for_bugfix(root, old_dir_name)
    new_state_path = root / ".workflow" / "state" / "bugfixes" / f"{new_dir_name}.yaml"
    if old_state_path is not None and old_state_path.exists():
        payload = load_simple_yaml(old_state_path)
        if not isinstance(payload, dict):
            payload = {}
        payload["id"] = old_id
        payload["title"] = new_title
        new_state_path.parent.mkdir(parents=True, exist_ok=True)
        save_simple_yaml(
            new_state_path,
            payload,
            ordered_keys=["id", "title", "stage", "status", "created_at", "started_at", "completed_at", "stage_timestamps", "description"],
        )
        if old_state_path != new_state_path:
            try:
                old_state_path.unlink()
            except OSError:
                pass

    runtime = load_requirement_runtime(root)
    save_requirement_runtime(root, runtime)

    print(f"Bugfix renamed: {old_dir_name} -> {new_dir_name}")
    return 0


def _extract_section(text: str, heading: str) -> str:
    """提取 Markdown 文本中包含 heading 关键词的 ## 章节内容（不含标题行本身）。"""
    lines = text.splitlines()
    in_section = False
    result: list[str] = []
    for line in lines:
        if line.startswith("## ") and heading in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("## "):
                break
            result.append(line)
    return "\n".join(result).strip()


def generate_requirement_artifact(root: Path, archive_target: Path, req_id: str, title: str) -> Path:
    """生成需求制品文档，输出到 artifacts/requirements/{req_id}-{title}.md。"""
    from datetime import date as _date
    git_branch = _get_git_branch(root)

    # 读取 requirement.md
    req_md_path = archive_target / "requirement.md"
    req_text = req_md_path.read_text(encoding="utf-8") if req_md_path.exists() else ""
    goal = _extract_section(req_text, "Goal") or _extract_section(req_text, "目标")
    scope = _extract_section(req_text, "Scope") or _extract_section(req_text, "范围")
    acceptance = _extract_section(req_text, "Acceptance") or _extract_section(req_text, "验收")

    # 读取各 change.md 构建变更列表
    change_lines: list[str] = []
    changes_dir = archive_target / "changes"
    if changes_dir.exists():
        for chg_dir in sorted(changes_dir.iterdir()):
            chg_md = chg_dir / "change.md"
            if not chg_md.exists():
                continue
            chg_text = chg_md.read_text(encoding="utf-8")
            chg_title = _extract_section(chg_text, "Title").splitlines()[0].strip() if _extract_section(chg_text, "Title") else chg_dir.name
            chg_goal_raw = _extract_section(chg_text, "Goal") or _extract_section(chg_text, "目标")
            chg_goal = (chg_goal_raw.splitlines()[0].strip() if chg_goal_raw else "")
            chg_id = chg_dir.name.split("-")[0] + "-" + chg_dir.name.split("-")[1] if "-" in chg_dir.name else chg_dir.name
            if chg_goal:
                change_lines.append(f"- **{chg_id}** {chg_title}：{chg_goal}")
            else:
                change_lines.append(f"- **{chg_id}** {chg_title}")

    # 读取 sessions 关键决策
    decisions_parts: list[str] = []
    sessions_dir = archive_target / "sessions"
    if sessions_dir.exists():
        for chg_dir in sorted(sessions_dir.iterdir()):
            if not chg_dir.is_dir():
                continue
            mem_path = chg_dir / "session-memory.md"
            if mem_path.exists():
                mem_text = mem_path.read_text(encoding="utf-8")
                decisions = _extract_section(mem_text, "关键决策") or _extract_section(mem_text, "Key Decisions")
                if decisions:
                    decisions_parts.append(f"**{chg_dir.name}**\n{decisions}")

    # 读取 done-report.md 遗留问题
    pending_issues = ""
    done_report_path = archive_target / "sessions" / "done-report.md"
    if done_report_path.exists():
        report_text = done_report_path.read_text(encoding="utf-8")
        pending_issues = _extract_section(report_text, "遗留") or _extract_section(report_text, "Pending")

    # 构建文档
    today = _date.today().isoformat()
    branch_label = git_branch or "unknown"
    sections: list[str] = [
        f"# {title}",
        "",
        f"> req-id: {req_id} | 完成时间: {today} | 分支: {branch_label}",
    ]
    if goal:
        sections += ["", "## 需求目标", "", goal]
    if scope:
        sections += ["", "## 交付范围", "", scope]
    if acceptance:
        sections += ["", "## 验收标准", "", acceptance]
    if change_lines:
        sections += ["", "## 变更列表", ""] + change_lines
    if decisions_parts:
        sections += ["", "## 关键设计决策", ""] + decisions_parts
    if pending_issues:
        sections += ["", "## 遗留问题与注意事项", "", pending_issues]

    out_dir = root / "artifacts" / (git_branch or "main") / "requirements"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{req_id}-{title}.md"
    out_path.write_text("\n".join(sections) + "\n", encoding="utf-8")
    return out_path


def _get_req_id(state: dict[str, object]) -> str:
    """Get requirement id from state, preferring 'id' over legacy 'req_id'."""
    return str(state.get("id", state.get("req_id", ""))).strip()


def _sync_stage_to_state_yaml(
    root: Path,
    operation_type: str,
    operation_target: str,
    new_stage: str,
) -> Path | None:
    """Sync `.workflow/state/{requirements,bugfixes}/{id}.yaml` 的 stage / status。

    req-26 / chg-03（AC-03）双写 helper：
    - 根据 ``operation_type``（requirement/bugfix/suggestion）选择 state 目录；
    - ``operation_target`` 为 id（如 ``req-26`` / ``bugfix-3``），按"直命中 id 字段
      或文件名 stem 前缀匹配 `{id}-`" 两种策略定位 state yaml；
    - 写回 ``stage``；若 ``new_stage == "done"`` 则同步 ``status = "done"`` 与
      ``completed_at``；若文件里存在/可初始化 ``stage_timestamps`` 则打一条时间戳。

    返回实际写入的文件路径（未命中任何 state yaml 则返回 ``None``，由调用方决定
    是否打日志，不抛异常，保持与旧 loop 一致的"best-effort"语义）。

    风格对齐 ``rename_bugfix`` / ``_state_yaml_for_requirement`` 的前缀匹配写法。
    """
    if not operation_target or not new_stage:
        return None
    sub = "bugfixes" if operation_type == "bugfix" else "requirements"
    state_dir = root / ".workflow" / "state" / sub
    if not state_dir.exists():
        return None

    target_path: Path | None = None
    target_state: dict[str, object] | None = None
    for state_file in sorted(state_dir.rglob("*.yaml")):
        state = load_simple_yaml(state_file)
        if not isinstance(state, dict):
            continue
        state_id = _get_req_id(state)
        stem = state_file.stem
        # 主匹配：id 严格相等，或文件名 stem 以 `{id}-` 开头（兼容 `{id}-{slug}.yaml`）。
        if (
            (state_id and state_id == operation_target)
            or stem == operation_target
            or stem.startswith(operation_target + "-")
        ):
            target_path = state_file
            target_state = state
            break

    if target_path is None or target_state is None:
        return None

    target_state["stage"] = new_stage
    if new_stage == "done":
        target_state["status"] = "done"
        target_state["completed_at"] = date.today().isoformat()

    # 若 state yaml 有 stage_timestamps 字段（或为空 dict），顺手打一条时间戳；
    # 文件里完全不存在该字段时，不主动创建，避免 schema 漂移。
    if "stage_timestamps" in target_state:
        existing = target_state.get("stage_timestamps")
        if not isinstance(existing, dict):
            existing = {}
        existing[new_stage] = datetime.now(timezone.utc).isoformat()
        target_state["stage_timestamps"] = existing

    save_simple_yaml(target_path, target_state)
    return target_path


def _check_plan_completion(plan_path: Path) -> tuple[bool, list[str]]:
    """
    检查 plan.md 所有步骤是否完成。

    Args:
        plan_path: plan.md 文件路径

    Returns:
        (is_complete, incomplete_steps)
        - is_complete: 所有步骤是否全部完成
        - incomplete_steps: 未完成步骤的描述列表
    """
    if not plan_path.exists():
        return False, [f"plan.md not found: {plan_path}"]

    content = plan_path.read_text(encoding="utf-8")
    incomplete_steps = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("- [ ]"):
            step_text = stripped[5:].strip()
            if step_text:
                incomplete_steps.append(step_text)

    return len(incomplete_steps) == 0, incomplete_steps


def list_done_requirements(root: Path) -> list[dict]:
    """返回 stage == 'done' 且尚未归档的需求与 bugfix 列表。

    req-28 / chg-03（AC-14）：同时扫 ``.workflow/state/requirements/`` 与
    ``.workflow/state/bugfixes/``，每条结果带 ``kind`` 字段（``req`` / ``bugfix``）。
    """
    results: list[dict] = []
    for sub, kind in (("requirements", "req"), ("bugfixes", "bugfix")):
        state_dir = root / ".workflow" / "state" / sub
        if not state_dir.exists():
            continue
        for req_file in sorted(state_dir.rglob("*.yaml")):
            state = load_simple_yaml(req_file)
            stage = str(state.get("stage", "")).strip()
            status = str(state.get("status", "")).strip()
            if stage == "done" and status != "archived":
                results.append({
                    "req_id": _get_req_id(state),
                    "title": str(state.get("title", "")).strip(),
                    "stage": stage,
                    "kind": kind,
                })
    return results


def list_active_requirements(root: Path) -> list[dict]:
    """返回 runtime active_requirements 中的需求列表，含 title 和 stage。"""
    runtime = load_requirement_runtime(root)
    active_ids = [str(r).strip() for r in runtime.get("active_requirements", [])]
    id_to_state: dict[str, dict] = {}
    for subdir in ["requirements", "bugfixes"]:
        state_dir = root / ".workflow" / "state" / subdir
        if state_dir.exists():
            for req_file in sorted(state_dir.rglob("*.yaml")):
                state = load_simple_yaml(req_file)
                req_id = _get_req_id(state)
                if req_id:
                    id_to_state[req_id] = state
    results = []
    for req_id in active_ids:
        state = id_to_state.get(req_id, {})
        results.append({
            "req_id": req_id,
            "title": str(state.get("title", "")).strip(),
            "stage": str(state.get("stage", "")).strip(),
        })
    return results


def _get_git_branch(root: Path) -> str:
    """读取当前 git 分支名，失败时返回空字符串。"""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = result.stdout.strip()
        return branch.replace("/", "-") if branch else ""
    except Exception:
        return ""


# 噪声文件名白名单（模块级常量，便于扩展）
# 用于 `resolve_requirement_root` / `resolve_archive_root` 判定"实质性非空"：
# 若目录下仅存在这些噪声文件（而无实质 req/change/archive 内容），视为空。
_REQUIREMENT_ROOT_NOISE_FILENAMES: frozenset[str] = frozenset({
    ".DS_Store",
    ".gitkeep",
    "Thumbs.db",
    ".keep",
})


def _has_substantive_content(p: Path) -> bool:
    """目录存在且过滤噪声后仍有子节点。仅检查直接子节点、不递归。"""
    if not p.exists() or not p.is_dir():
        return False
    try:
        return any(
            child.name not in _REQUIREMENT_ROOT_NOISE_FILENAMES
            for child in p.iterdir()
        )
    except OSError:
        return False


def resolve_requirement_root(root: Path) -> Path:
    """返回当前仓库 requirement 产出的根目录，按优先级降级：

    1. ``artifacts/{branch}/requirements``（branch 由 ``_get_git_branch`` 解析，失败兜底 ``main``）
    2. ``artifacts/requirements``（兼容未启用 branch 的过渡形态）
    3. ``.workflow/flow/requirements``（legacy，仅老仓兼容；降级时 stderr 告警，
       并提示用户运行 ``harness migrate requirements``）

    选择策略：返回"目录存在且实质性非空（过滤 ``_REQUIREMENT_ROOT_NOISE_FILENAMES``
    后仍有子节点）"的最高优先级路径；若全部不存在或全部仅含噪声文件，返回第 1 级
    路径（让调用方负责创建）。

    helper 不做 ``mkdir``，创建责任留给调用方。
    """
    branch = _get_git_branch(root) or "main"
    primary = root / "artifacts" / branch / "requirements"
    secondary = root / "artifacts" / "requirements"
    legacy = root / ".workflow" / "flow" / "requirements"

    if _has_substantive_content(primary):
        return primary
    if _has_substantive_content(secondary):
        try:
            display = secondary.relative_to(root)
        except ValueError:
            display = secondary
        print(
            f"[harness] warning: using legacy path {display}; "
            f"run `harness migrate requirements` to consolidate.",
            file=sys.stderr,
        )
        return secondary
    if _has_substantive_content(legacy):
        try:
            display = legacy.relative_to(root)
        except ValueError:
            display = legacy
        print(
            f"[harness] warning: using legacy path {display}; "
            f"run `harness migrate requirements` to consolidate.",
            file=sys.stderr,
        )
        return legacy
    return primary  # 新仓 / 空仓 / 仅噪声 → 落到新路径


def resolve_archive_root(root: Path, prefer_legacy: bool = False) -> Path:
    """返回归档产出根目录。

    req-29 / chg-01（AC-03）：**primary 始终优先**，legacy 仅在显式 opt-in
    时使用。默认判据链：

    1. ``artifacts/{branch}/archive``（primary，默认）
    2. ``.workflow/flow/archive``（legacy，仅在显式 opt-in 时返回）

    opt-in 机制（二者任一命中即视为 opt-in）：

    - 参数 ``prefer_legacy=True``
    - 环境变量 ``HARNESS_ARCHIVE_LEGACY=1``

    **默认行为**（未 opt-in）：无论 legacy 是否非空，都返回 primary；若 legacy
    非空，额外在 stderr 打印一次迁移提示（``run `harness migrate archive` to
    consolidate``），引导用户用 chg-02 的 migrate 命令把历史归档搬到 primary。

    **opt-in 行为**：若 legacy 非空，返回 legacy（保留原告警）；若 legacy 空，
    仍返回 primary（opt-in 也无法凭空制造 legacy 数据）。

    helper 不做 ``mkdir``，创建责任留给调用方。
    """
    branch = _get_git_branch(root) or "main"
    primary = root / "artifacts" / branch / "archive"
    legacy = root / ".workflow" / "flow" / "archive"

    # 环境变量 opt-in：只有值严格等于 "1" 时生效，避免 "0"/空字符串等误触发。
    env_opt_in = os.environ.get("HARNESS_ARCHIVE_LEGACY", "") == "1"
    opt_in = prefer_legacy or env_opt_in

    legacy_nonempty = _has_substantive_content(legacy)

    if opt_in and legacy_nonempty:
        try:
            display = legacy.relative_to(root)
        except ValueError:
            display = legacy
        print(
            f"[harness] warning: using legacy archive path {display}; "
            f"run `harness migrate archive` to consolidate.",
            file=sys.stderr,
        )
        return legacy

    # 默认：primary 优先。若 legacy 非空，打印一次迁移提示（不降级）。
    if legacy_nonempty:
        try:
            display = legacy.relative_to(root)
        except ValueError:
            display = legacy
        print(
            f"[harness] notice: using primary archive path; legacy at {display} "
            f"has data, run `harness migrate archive` to consolidate.",
            file=sys.stderr,
        )
    return primary


def resolve_bugfix_root(root: Path) -> Path:
    """返回 bugfix 工作目录根（非归档）。

    req-28 / chg-03：与 ``resolve_requirement_root`` 对称，用于定位 bugfix
    活跃目录，供 ``archive_requirement`` 在 bugfix 分流时找到源目录。

    优先级：
      1. ``artifacts/{branch}/bugfixes``
      2. ``artifacts/bugfixes``（过渡形态）
      3. ``.workflow/flow/bugfixes``（legacy）

    与 ``resolve_requirement_root`` 一致，helper 不做 mkdir；全不存在时返回
    primary 路径，由调用方负责创建。
    """
    branch = _get_git_branch(root) or "main"
    primary = root / "artifacts" / branch / "bugfixes"
    secondary = root / "artifacts" / "bugfixes"
    legacy = root / ".workflow" / "flow" / "bugfixes"

    if _has_substantive_content(primary):
        return primary
    if _has_substantive_content(secondary):
        return secondary
    if _has_substantive_content(legacy):
        return legacy
    return primary


def migrate_requirements(root: Path, dry_run: bool = False) -> int:
    """把 legacy 路径下的 requirement 目录搬到 ``artifacts/{branch}/requirements``。

    扫描源（按优先级）：
      1. ``root / ".workflow" / "flow" / "requirements"``
      2. ``root / "artifacts" / "requirements"``
    目标：
      ``root / "artifacts" / {branch} / "requirements"``

    行为：
      - 源目录不存在或仅含噪声 → 跳过
      - 目标已有同名目录 → 报错、不覆盖，计入冲突
      - ``src == dst`` 的边界（幂等） → 跳过
      - ``dry_run=True`` → 仅打印计划，rc=0（即使存在潜在冲突）
      - 返回 rc：无冲突且完成 → 0；有冲突 → 1
    """
    branch = _get_git_branch(root) or "main"
    dst_root = root / "artifacts" / branch / "requirements"
    src_legacy = root / ".workflow" / "flow" / "requirements"
    src_mid = root / "artifacts" / "requirements"

    migrated: list[str] = []
    conflicts: list[str] = []
    skipped_idempotent: list[str] = []
    dry_run_planned: list[str] = []

    if not dry_run:
        dst_root.mkdir(parents=True, exist_ok=True)

    def _process_source(src_root: Path) -> None:
        if not src_root.exists() or not src_root.is_dir():
            return
        # 若源整体为空或仅含噪声 → 跳过
        if not _has_substantive_content(src_root):
            return
        for child in sorted(src_root.iterdir()):
            if child.name in _REQUIREMENT_ROOT_NOISE_FILENAMES:
                continue
            if not child.is_dir():
                continue
            dst = dst_root / child.name
            # src == dst 幂等边界（解析为同一物理目录）
            try:
                if child.resolve() == dst.resolve():
                    skipped_idempotent.append(child.name)
                    continue
            except OSError:
                pass
            if dst.exists():
                conflicts.append(child.name)
                print(
                    f"[migrate] conflict: {dst} already exists, skipped; "
                    f"please manually reconcile `{child}` and `{dst}` "
                    f"(rename or merge) before retrying.",
                    file=sys.stderr,
                )
                continue
            if dry_run:
                dry_run_planned.append(child.name)
                print(f"[migrate] (dry-run) {child} -> {dst}")
                continue
            print(f"[migrate] {child} -> {dst}")
            shutil.move(str(child), str(dst))
            migrated.append(child.name)

    _process_source(src_legacy)
    _process_source(src_mid)

    if dry_run:
        print(
            f"[migrate] done (dry-run): {len(dry_run_planned)} planned, "
            f"{len(conflicts)} conflict(s), {len(skipped_idempotent)} already-at-target"
        )
        return 0

    total = len(migrated) + len(conflicts) + len(skipped_idempotent)
    if total == 0:
        print("[migrate] nothing to migrate")
        return 0

    print(
        f"[migrate] done: {len(migrated)} migrated, "
        f"{len(conflicts)} skipped (conflict), "
        f"{len(skipped_idempotent)} already-at-target"
    )
    return 1 if conflicts else 0


def migrate_archive(root: Path, dry_run: bool = False) -> int:
    """把 legacy 归档目录搬到 ``artifacts/{branch}/archive/``（req-29 / chg-02, AC-04）。

    **源**：``.workflow/flow/archive/`` 下两种形态：

      1. 带分支前缀：``.workflow/flow/archive/<branch>/{requirements,bugfixes}/<dir>/``
         （历史上 archive_requirement 在带 folder=branch 拼接时产生的）
      2. 裸形态：``.workflow/flow/archive/{requirements,bugfixes}/<dir>/``
         （chg-01 前的默认 legacy 布局）

    **目标**：统一落到 ``artifacts/{branch}/archive/{requirements,bugfixes}/<dir>/``；
    当前仓库分支由 ``_get_git_branch(root)`` 解析，失败兜底 ``main``。注意：带分支
    前缀的 legacy 条目会被"重新归位"到当前 git 分支下——保留 ``{requirements,
    bugfixes}/<dir>`` 这一层相对结构。

    **策略**：
      - 逐条目 ``shutil.move`` 整目录（由调用方保证 dry_run 时不动文件）。
      - 目标已存在 → 记 conflict、跳过、不覆盖。
      - ``src == dst`` 幂等边界 → 记 already-at-target、跳过。
      - 迁移完保留 ``.workflow/flow/archive/`` 空父目录作为退路，不删。
      - ``dry_run=True`` → 仅打印 plan、rc=0、不动文件。

    **返回**：rc=0（无冲突） / rc=1（有冲突；仍继续处理其他条目）。
    """
    branch = _get_git_branch(root) or "main"
    legacy_root = root / ".workflow" / "flow" / "archive"
    dst_root = root / "artifacts" / branch / "archive"

    migrated: list[str] = []
    conflicts: list[str] = []
    skipped_idempotent: list[str] = []
    dry_run_planned: list[str] = []

    if not dry_run and legacy_root.exists():
        dst_root.mkdir(parents=True, exist_ok=True)

    def _plan_pairs() -> list[tuple[Path, Path]]:
        """枚举 (src, dst) 对：只收集两种合法形态下的 requirements/bugfixes 子条目。"""
        if not legacy_root.exists() or not legacy_root.is_dir():
            return []
        pairs: list[tuple[Path, Path]] = []

        def _collect_from_kind_root(kind_root: Path, kind: str) -> None:
            """从 ``<some>/<kind>/`` 目录收集直接子目录作为迁移单元。"""
            if not kind_root.exists() or not kind_root.is_dir():
                return
            for child in sorted(kind_root.iterdir()):
                if child.name in _REQUIREMENT_ROOT_NOISE_FILENAMES:
                    continue
                if not child.is_dir():
                    continue
                dst = dst_root / kind / child.name
                pairs.append((child, dst))

        # 形态 1：带分支前缀 `<branch>/{requirements,bugfixes}/<dir>`
        for branch_dir in sorted(legacy_root.iterdir()):
            if branch_dir.name in _REQUIREMENT_ROOT_NOISE_FILENAMES:
                continue
            if not branch_dir.is_dir():
                continue
            if branch_dir.name in ("requirements", "bugfixes"):
                continue  # 形态 2，后面单独处理
            # branch_dir 是一个分支名（不强校验名称，保留任意分支子树）
            for kind in ("requirements", "bugfixes"):
                _collect_from_kind_root(branch_dir / kind, kind)

        # 形态 2：裸 `requirements/`、`bugfixes/` 子目录
        for kind in ("requirements", "bugfixes"):
            _collect_from_kind_root(legacy_root / kind, kind)

        return pairs

    pairs = _plan_pairs()

    for src, dst in pairs:
        label = f"{dst.parent.name}/{src.name}"  # e.g. "requirements/req-26-xxx"

        # src == dst 幂等边界（罕见：调用者把 legacy 指向 primary）
        try:
            if src.resolve() == dst.resolve():
                skipped_idempotent.append(label)
                continue
        except OSError:
            pass

        if dst.exists():
            conflicts.append(label)
            print(
                f"[migrate] conflict: {dst} already exists, skipped; "
                f"please manually reconcile `{src}` and `{dst}` "
                f"(rename or merge) before retrying.",
                file=sys.stderr,
            )
            continue

        if dry_run:
            dry_run_planned.append(label)
            print(f"[migrate] (dry-run) {src} -> {dst}")
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        print(f"[migrate] {src} -> {dst}")
        shutil.move(str(src), str(dst))
        migrated.append(label)

    if dry_run:
        print(
            f"[migrate] done (dry-run): {len(dry_run_planned)} planned, "
            f"{len(conflicts)} conflict(s), {len(skipped_idempotent)} already-at-target"
        )
        return 0

    total = len(migrated) + len(conflicts) + len(skipped_idempotent)
    if total == 0:
        print("[migrate] nothing to migrate")
        return 0

    print(
        f"[migrate] done: {len(migrated)} migrated, "
        f"{len(conflicts)} skipped (conflict), "
        f"{len(skipped_idempotent)} already-at-target"
    )
    return 1 if conflicts else 0


def archive_requirement(
    root: Path,
    requirement_name: str,
    folder: str = "",
    force_done: bool = False,
) -> int:
    """归档 requirement 或 bugfix。

    req-28 / chg-03（AC-14）：按 id 前缀分流。
      - ``req-*`` → ``artifacts/{branch}/archive/requirements/<dir>``（保留原行为，
        primary 形态下不再拼 ``folder=branch`` 避免双层 branch，legacy 保持）。
      - ``bugfix-*`` → ``artifacts/{branch}/archive/bugfixes/<dir>``，源目录从
        ``resolve_bugfix_root`` 定位，state yaml 落 ``state/bugfixes/``。

    ``force_done`` 用于 sweep 历史活跃 bugfix：把目标 state yaml 的 ``stage`` 强置
    为 ``done``、``status`` 设为 ``done``、``completed_at`` 填当前时间，然后走正常
    归档路径。仅对 bugfix 生效；对 requirement 是 no-op（保留接口对称）。
    """
    from datetime import datetime as _dt

    runtime = load_requirement_runtime(root)
    current_branch = _get_git_branch(root) or "main"

    # --- id 前缀分流 ---
    raw_ref = (requirement_name or "").strip()
    is_bugfix = raw_ref.startswith("bugfix-") or (
        # 容错：调用者传入完整目录名（含 slug）
        raw_ref.startswith("bugfix-") and "-" in raw_ref
    )
    # 真正的判定：凡是以 `bugfix-` 开头即视为 bugfix。
    is_bugfix = raw_ref.startswith("bugfix-")
    kind_label = "bugfix" if is_bugfix else "requirement"

    if is_bugfix:
        source_root = resolve_bugfix_root(root)
        state_subdir = "bugfixes"
        archive_subdir = "bugfixes"
    else:
        source_root = resolve_requirement_root(root)
        state_subdir = "requirements"
        archive_subdir = "requirements"

    req_dir = resolve_requirement_reference(source_root, raw_ref, "cn")
    if not req_dir:
        raise SystemExit(f"{kind_label.capitalize()} does not exist: {requirement_name}")

    # --- force-done：在移动目录前改写 state yaml ---
    state_yaml_path: Path | None = None
    if is_bugfix:
        state_dir_for_force = root / ".workflow" / "state" / "bugfixes"
        if state_dir_for_force.exists():
            for yaml_path in sorted(state_dir_for_force.rglob("*.yaml")):
                st = load_simple_yaml(yaml_path)
                st_id = _get_req_id(st)
                stem = yaml_path.stem
                if (
                    (st_id and st_id == raw_ref)
                    or stem == raw_ref
                    or stem.startswith(raw_ref + "-")
                    or stem == req_dir.name
                    or (st_id and st_id in req_dir.name)
                ):
                    state_yaml_path = yaml_path
                    break
        if state_yaml_path is None:
            # 无 state yaml 时不硬失败；但 force_done 没有目标，直接忽略。
            pass
        else:
            state_data = load_simple_yaml(state_yaml_path)
            stage_val = str(state_data.get("stage", "")).strip()
            if stage_val != "done":
                if not force_done:
                    raise SystemExit(
                        f"Bugfix {raw_ref} stage is '{stage_val}', not 'done'. "
                        f"Use --force-done to archive anyway."
                    )
                state_data["stage"] = "done"
                state_data["status"] = "done"
                state_data["completed_at"] = _dt.now().isoformat(timespec="seconds")
                save_simple_yaml(state_yaml_path, state_data)
                print(f"[archive] force-done: {state_yaml_path.name} stage -> done")

    # --- 目标路径计算 ---
    # 若未传 folder，读取 git branch 作为默认
    if not folder:
        folder = current_branch

    # req-26 / chg-04 AC-05：修复归档路径双层 branch。
    # ``resolve_archive_root`` 的 primary 分支（``artifacts/{branch}/archive``）已经
    # 把 branch 段烙在路径里；若调用方再拼一次 ``folder=branch``，就会产生
    # ``artifacts/main/archive/main/req-xx`` 的双层 branch。
    # 修复策略：若 archive_base 的直接父目录已是当前 branch（primary 形态），
    # 则跳过这一层拼接；legacy 形态（``.workflow/flow/archive``）不含 branch，
    # 照旧拼一层 folder。历史已存在的双层 branch 目录保持不动（AC-05 Excluded）。
    archive_base = resolve_archive_root(root)

    def _archive_base_already_has_branch(base: Path, branch: str) -> bool:
        # primary 形态：``<root>/artifacts/{branch}/archive``，base.parent.name == branch
        if not branch:
            return False
        try:
            return base.parent.name == branch and base.name == "archive"
        except Exception:
            return False

    if folder and _archive_base_already_has_branch(archive_base, current_branch) and folder == current_branch:
        # primary：base 已经含 branch，折叠一层避免双拼
        target_parent = archive_base / archive_subdir
    else:
        # legacy / 自定义 folder：保持原 ``archive/{folder}/<dir>`` 结构
        # 对 bugfix 仍在 folder 下再拼一层 ``bugfixes/``，区分 requirement / bugfix
        if folder:
            target_parent = archive_base / folder / archive_subdir
        else:
            target_parent = archive_base / archive_subdir
    target_parent.mkdir(parents=True, exist_ok=True)

    target = target_parent / req_dir.name
    shutil.move(str(req_dir), str(target))

    # Update state/{sub}/*.yaml and migrate to archive
    req_state_dir = root / ".workflow" / "state" / state_subdir
    archived_req_id = ""
    if req_state_dir.exists():
        for req_file in sorted(req_state_dir.rglob("*.yaml")):
            state = load_simple_yaml(req_file)
            req_id_val = _get_req_id(state)
            if req_file.stem == req_dir.name or (req_id_val and req_id_val in req_dir.name):
                archived_req_id = req_id_val
                state["status"] = "archived"
                save_simple_yaml(req_file, state)
                # Migrate state.yaml to archive directory
                shutil.move(str(req_file), str(target / "state.yaml"))
                break

    # Update runtime active_requirements
    active_reqs = [str(r) for r in runtime.get("active_requirements", []) if str(r) != archived_req_id]
    runtime["active_requirements"] = active_reqs
    current_req = str(runtime.get("current_requirement", "")).strip()
    # req-28 / chg-03：归档 bugfix 不应意外切走 current_requirement（如主 req-28）。
    # 仅当 current_requirement 精确等于被归档 id（或目录名中含之）时才清空/重定向。
    if current_req == archived_req_id or (archived_req_id and current_req == raw_ref):
        runtime["current_requirement"] = active_reqs[0] if active_reqs else ""
    save_requirement_runtime(root, runtime)

    # Migrate state/sessions/{id}/ to archive directory（仅 requirement 分支保留 sessions 迁移）
    if archived_req_id and not is_bugfix:
        sessions_src = root / ".workflow" / "state" / "sessions" / archived_req_id
        if sessions_src.exists():
            sessions_dst = target / "sessions"
            shutil.move(str(sessions_src), str(sessions_dst))
            print(f"Migrated sessions: {sessions_dst}")

    # Clean up residual active directory
    residual_req_dir = source_root / req_dir.name
    if residual_req_dir.exists():
        shutil.rmtree(str(residual_req_dir))
        try:
            print(f"Cleaned residual: {residual_req_dir.relative_to(root)}")
        except ValueError:
            print(f"Cleaned residual: {residual_req_dir}")

    # Generate artifact document（仅 requirement 分支；bugfix 目前不强求 artifact 文档）
    if archived_req_id and not is_bugfix:
        req_title = re.sub(r"^req-\d+-", "", req_dir.name)
        try:
            artifact_path = generate_requirement_artifact(root, target, archived_req_id, req_title)
            print(f"Generated artifact: {artifact_path}")
        except Exception as exc:
            print(f"Warning: artifact generation failed: {exc}")

    print(f"Archived {kind_label}: {req_dir.name}")
    print(f"Archive path: {target}")

    # Git auto-commit prompt
    try:
        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if git_check.returncode == 0 and git_check.stdout.strip() == "true":
            answer = input("Auto-commit archive changes? [y/N]: ").strip().lower()
            if answer in ("y", "yes"):
                subprocess.run(["git", "add", "-A"], cwd=root, check=False)
                commit_msg = f"archive: {req_dir.name}"
                commit_result = subprocess.run(
                    ["git", "commit", "-m", commit_msg],
                    cwd=root,
                    capture_output=True,
                    text=True,
                )
                if commit_result.returncode == 0:
                    print(f"Committed: {commit_msg}")
                    push_answer = input("Push to remote? [y/N]: ").strip().lower()
                    if push_answer in ("y", "yes"):
                        push_result = subprocess.run(
                            ["git", "push"],
                            cwd=root,
                            capture_output=True,
                            text=True,
                        )
                        if push_result.returncode == 0:
                            print("Pushed to remote.")
                        else:
                            print(f"Push failed: {push_result.stderr.strip()}")
                else:
                    print(f"Commit failed: {commit_result.stderr.strip()}")
    except EOFError:
        pass
    except Exception as exc:
        print(f"Warning: git auto-commit check failed: {exc}")

    return 0


def validate_requirement(root: Path) -> int:
    runtime = load_requirement_runtime(root)
    req_id = str(runtime.get("current_requirement", "")).strip()
    if not req_id:
        print("No active requirement.")
        return 1

    requirements_dir = resolve_requirement_root(root)
    req_dir = resolve_requirement_reference(requirements_dir, req_id, "cn")
    if not req_dir:
        print(f"Requirement not found: {req_id}")
        return 1

    changes_dir = req_dir / "changes"
    if not changes_dir.exists():
        print(f"No changes found for {req_id}")
        return 0

    all_ok = True
    for change_path in sorted(changes_dir.iterdir()):
        if not change_path.is_dir():
            continue
        missing: list[str] = []
        if not (change_path / "testing-report.md").exists():
            missing.append("testing-report.md")
        if not (change_path / "acceptance-report.md").exists():
            missing.append("acceptance-report.md")
        if missing:
            all_ok = False
            print(f"[{change_path.name}] Missing: {', '.join(missing)}")

    if all_ok:
        print(f"Artifact validation passed for {req_id}")
    else:
        print("Artifact validation failed.")
        return 1

    # Python syntax check
    compile_errors: list[tuple[str, str]] = []
    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        parts = rel.parts
        if "__pycache__" in parts or ".venv" in parts or "venv" in parts or ".tox" in parts:
            continue
        try:
            py_compile.compile(str(py_file), doraise=True)
        except Exception as exc:
            compile_errors.append((str(rel), str(exc)))

    if compile_errors:
        print("\nCompile check failed:")
        for path, msg in compile_errors:
            print(f"  {path}: {msg}")
        return 1

    print("Compile check passed.")
    return 0


def workflow_status(root: Path) -> int:
    runtime = load_requirement_runtime(root)
    current_requirement = str(runtime.get("current_requirement", "")).strip()
    locked_requirement = str(runtime.get("locked_requirement", "")).strip()
    effective_requirement = locked_requirement or current_requirement
    print(f"current_requirement: {current_requirement or '(none)'}")
    print(f"stage: {str(runtime.get('stage', '')).strip() or '(none)'}")
    print(f"conversation_mode: {runtime.get('conversation_mode', 'open')}")
    print(f"locked_requirement: {locked_requirement or '(none)'}")
    print(f"locked_stage: {str(runtime.get('locked_stage', '')).strip() or '(none)'}")
    print(f"current_regression: {str(runtime.get('current_regression', '')).strip() or '(none)'}")
    active_requirements = runtime.get("active_requirements", [])
    if isinstance(active_requirements, list):
        rendered_active = ", ".join(str(item) for item in active_requirements) or "(none)"
        print(f"active_requirements: {rendered_active}")
    if effective_requirement:
        requirements_dir = root / ".workflow" / "state" / "requirements"
        match = next(
            (
                path
                for path in sorted(requirements_dir.glob("*.yaml"))
                if _get_req_id(load_simple_yaml(path)) == effective_requirement
            ),
            None,
        )
        if match is not None:
            state = load_simple_yaml(match)
            title = str(state.get("title", "")).strip()
            status = str(state.get("status", "")).strip()
            req_stage = str(state.get("stage", "")).strip()
            if title:
                print(f"requirement_title: {title}")
            if status:
                print(f"requirement_status: {status}")
            if req_stage:
                print(f"requirement_stage: {req_stage}")
    return 0


def workflow_next(root: Path, execute: bool = False) -> int:
    runtime = load_requirement_runtime(root)
    current_stage = str(runtime.get("stage", "")).strip()
    operation_type = str(runtime.get("operation_type", "")).strip()

    # 根据 operation_type 选择对应的 stage 序列
    if operation_type == "bugfix":
        sequence = BUGFIX_SEQUENCE
    elif operation_type == "suggestion":
        sequence = SUGGESTION_SEQUENCE
    else:
        sequence = WORKFLOW_SEQUENCE

    if not current_stage:
        raise SystemExit("No active workflow stage. Run `harness requirement <title>` to begin.")
    if current_stage == "done":
        raise SystemExit("Workflow is already complete.")
    if current_stage not in sequence:
        raise SystemExit(f"Unknown stage: {current_stage}")

    idx = sequence.index(current_stage)
    if current_stage == "ready_for_execution" and not execute:
        raise SystemExit("Workflow is ready_for_execution. Run `harness next --execute` to confirm execution start.")

    next_stage = sequence[idx + 1] if idx + 1 < len(sequence) else current_stage

    prev_entered_at = str(runtime.get("stage_entered_at", ""))
    runtime["stage"] = next_stage
    runtime["stage_entered_at"] = datetime.now(timezone.utc).isoformat()

    # req-26 / chg-03（AC-03）：state yaml 双写同步。
    # 旧实现只在 runtime.yaml 提供 `operation_target` 时才写回；真实现场（runtime.yaml
    # 仅有 `current_requirement`、无 `operation_target`）会完全跳过写回，导致
    # requirement 的 state yaml 始终停留在 requirement_review，与 runtime 不一致。
    # 这里回退顺序：operation_target → current_requirement。保证 stage 推进必写。
    operation_target = str(runtime.get("operation_target", "")).strip()
    if not operation_target:
        operation_target = str(runtime.get("current_requirement", "")).strip()
    _sync_stage_to_state_yaml(root, operation_type, operation_target, next_stage)

    save_requirement_runtime(root, runtime)

    if next_stage == "done" and operation_target:
        extract_suggestions_from_done_report(root, operation_target)
        print("Review `context/experience/stage/` and update relevant stage experience before archiving.")

    duration_seconds: float | None = None
    if prev_entered_at:
        try:
            entered = datetime.fromisoformat(prev_entered_at)
            duration_seconds = (datetime.now(timezone.utc) - entered).total_seconds()
        except (ValueError, TypeError):
            pass
    record_feedback_event(root, "stage_duration", {
        "stage": current_stage,
        "duration_seconds": duration_seconds if duration_seconds is not None else 0,
    })
    record_feedback_event(root, "stage_advance", {
        "from_stage": current_stage,
        "to_stage": next_stage,
    })
    print(f"Workflow advanced to {next_stage}")
    return 0


def workflow_fast_forward(root: Path) -> int:
    runtime = load_requirement_runtime(root)
    from_stage = str(runtime.get("stage", "")).strip()
    operation_type = str(runtime.get("operation_type", "")).strip()
    operation_target = str(runtime.get("operation_target", "")).strip()

    # 根据 operation_type 确定目标 stage
    if operation_type == "bugfix":
        target_stage = "executing"
    elif operation_type == "suggestion":
        target_stage = "apply"
    else:
        target_stage = "ready_for_execution"

    runtime["stage"] = target_stage
    runtime["stage_entered_at"] = datetime.now(timezone.utc).isoformat()
    runtime["ff_mode"] = False  # ff 单次生效

    # req-26 / chg-03（AC-03）：ff 也复用同一 helper，target 回退 current_requirement。
    if not operation_target:
        operation_target = str(runtime.get("current_requirement", "")).strip()
    _sync_stage_to_state_yaml(root, operation_type, operation_target, target_stage)

    save_requirement_runtime(root, runtime)
    record_feedback_event(root, "stage_skip", {"from_stage": from_stage})
    record_feedback_event(root, "ff", {"from_stage": from_stage})
    print(f"Workflow advanced to {target_stage}")
    return 0


def enter_workflow(root: Path, req_id: str = "") -> int:
    runtime = load_requirement_runtime(root)
    if req_id:
        runtime["current_requirement"] = req_id
    runtime = set_conversation_mode(runtime, conversation_mode="harness")
    save_requirement_runtime(root, runtime)
    print("Entered harness mode.")

    current_req = str(runtime.get("current_requirement", "")).strip()
    if current_req:
        sessions_base = root / ".workflow" / "state" / "sessions" / current_req
        if sessions_base.exists():
            mem_files = sorted(sessions_base.rglob("session-memory.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            if mem_files:
                latest_mem = mem_files[0]
                content = latest_mem.read_text(encoding="utf-8")
                summary_lines: list[str] = []
                in_summary = False
                for line in content.splitlines():
                    if line.strip().startswith("## ") and ("摘要" in line or "Summary" in line or "结果" in line):
                        in_summary = True
                        summary_lines.append(line.strip())
                        continue
                    if in_summary:
                        if line.strip().startswith("## "):
                            break
                        summary_lines.append(line.rstrip())
                if summary_lines:
                    print("\n【上次对话摘要】")
                    for line in summary_lines:
                        if line:
                            print(line)
                else:
                    print(f"\n【提示】找到会话记录 {latest_mem.relative_to(root)}，但未提取到摘要区块。")
            else:
                print(f"\n【提示】当前需求 {current_req} 暂无会话记录。")
        else:
            print(f"\n【提示】当前需求 {current_req} 暂无会话记录。")

    return 0


def exit_workflow(root: Path) -> int:
    runtime = load_requirement_runtime(root)
    runtime = exit_harness_mode(runtime)
    save_requirement_runtime(root, runtime)
    print("Exited harness mode.")
    return 0


def get_skill_template_root() -> Path:
    """Get the skill template root directory.

    Returns the full skill template at `assets/skill/`, which is the SAME
    source used by `install_local_skills()` for codex/claude/qoder. This
    keeps all four agents' `.{agent}/skills/harness/` trees structurally
    symmetric (bugfix-5).

    Agent-specific notes (from `skills/harness/agent/{agent}.md`) are
    layered on top by `install_agent()` via `get_agent_notes_root()`.
    """
    return Path(str(SKILL_ROOT))


def get_agent_notes_root() -> Path:
    """Get the directory holding per-agent notes to layer on top of the
    full skill template (bugfix-5)."""
    return Path(__file__).resolve().parent / "skills" / "harness" / "agent"


def get_agent_skill_path(root: Path, agent: str) -> Path:
    """Get the target skill path for an agent."""
    agent_dir_map = {
        "kimi": root / ".kimi" / "skills" / "harness",
        "claude": root / ".claude" / "skills" / "harness",
        "codex": root / ".codex" / "skills" / "harness",
        "qoder": root / ".qoder" / "skills" / "harness",
    }
    return agent_dir_map.get(agent, root / f".{agent}" / "skills" / "harness")


def install_agent(root: Path, agent: str) -> int:
    """Install harness skill to target agent directory.

    Args:
        root: Repository root
        agent: Target agent (kimi, claude, codex, qoder)

    Returns:
        0 on success, non-zero on failure
    """
    # If .workflow/ is missing (e.g. a freshly `git init`-ed empty repo),
    # transparently run `harness init` first so that `harness install` works
    # as the single documented entry point (per README / SKILL.md). This fixes
    # bugfix-3: previously install_agent() would hard-fail with
    # "Harness workspace is missing" on an empty repo, contradicting the docs.
    workflow_dir = root / ".workflow"
    workflow_context_dir = workflow_dir / "context"
    if not workflow_dir.exists() or not workflow_context_dir.exists():
        print("No .workflow/ found, running harness init first...")
        # Seed AGENTS.md for non-claude agents, CLAUDE.md for claude.
        init_repo(
            root,
            write_agents=(agent in ("codex", "qoder", "kimi")),
            write_claude=(agent == "claude"),
        )
        # Ensure config is in place for downstream helpers.
        ensure_config(root)
    else:
        ensure_harness_root(root)

    template_root = get_skill_template_root()
    if not template_root.exists():
        raise SystemExit(f"Skill template not found: {template_root}")

    target_path = get_agent_skill_path(root, agent)
    template_skill = template_root / "SKILL.md"
    target_skill = target_path / "SKILL.md"

    # Build the merged "virtual" template: full skill tree + per-agent note
    # layered on top (bugfix-5). `overlay_files` maps relative path → source
    # file on disk. Files in the overlay win over the base template on any
    # conflict, so agent-specific notes (e.g. `agent/kimi.md`) are always
    # rendered.
    overlay_files: dict[Path, Path] = {}
    agent_notes_root = get_agent_notes_root()
    agent_note = agent_notes_root / f"{agent}.md"
    if agent_note.exists():
        overlay_files[Path("agent") / f"{agent}.md"] = agent_note

    def _iter_sources() -> list[tuple[Path, Path]]:
        """Yield (relative_path, absolute_source) pairs for the merged template.

        The base template contributes every file; overlays replace any
        matching relative path. Transient artifacts (`__pycache__`,
        `*.pyc`, `.DS_Store`) are excluded to keep the installed tree
        deterministic.
        """
        seen: dict[Path, Path] = {}
        for template_file in sorted(template_root.rglob("*")):
            if not template_file.is_file():
                continue
            rel_path = template_file.relative_to(template_root)
            parts = rel_path.parts
            if "__pycache__" in parts:
                continue
            if template_file.suffix == ".pyc":
                continue
            if template_file.name == ".DS_Store":
                continue
            seen[rel_path] = template_file
        # Overlay (agent-specific notes) on top
        for rel_path, src in overlay_files.items():
            seen[rel_path] = src
        return sorted(seen.items(), key=lambda kv: str(kv[0]))

    merged_sources = _iter_sources()
    merged_rel_paths = {rel for rel, _ in merged_sources}

    # Check for existing skill files
    changes: list[dict[str, str]] = []

    if target_path.exists():
        # Scan for existing files
        for existing_file in sorted(target_path.rglob("*")):
            if existing_file.is_file():
                rel_path = existing_file.relative_to(target_path)
                if rel_path not in merged_rel_paths:
                    changes.append({"type": "delete", "path": str(rel_path)})
                else:
                    src = dict(merged_sources)[rel_path]
                    src_content = src.read_text(encoding="utf-8")
                    # Apply the same template rendering used on write so that
                    # already-rendered files don't appear dirty.
                    src_rendered = src_content.replace("{AGENT_NAME}", agent).replace(
                        "{SKILL_DIR}", str(target_path)
                    )
                    if existing_file.read_text(encoding="utf-8") != src_rendered:
                        changes.append({"type": "modify", "path": str(rel_path)})

    # Check for new files
    for rel_path, _src in merged_sources:
        target_file = target_path / rel_path
        if not target_file.exists():
            changes.append({"type": "add", "path": str(rel_path)})

    # Show changes
    if changes:
        print("Changes detected:")
        for change in changes:
            print(f"  [{change['type']}] {change['path']}")
    else:
        print("No changes detected. Skill is up to date.")
        return 0

    # Create target directory
    target_path.mkdir(parents=True, exist_ok=True)

    # Copy merged template files (base + agent overlay)
    for rel_path, src in merged_sources:
        target_file = target_path / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        # Non-text files (e.g. compiled .pyc) would crash read_text; filter
        # to extensions we know are text. Binary assets are not expected in
        # the skill template, but guard anyway.
        try:
            content = src.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            shutil.copy2(src, target_file)
            continue
        # Render template variables
        content = content.replace("{AGENT_NAME}", agent)
        content = content.replace("{SKILL_DIR}", str(target_path))
        target_file.write_text(content, encoding="utf-8")

    print(f"Installed harness skill to {target_path.relative_to(root)}")

    # Write bootstrap instruction to entry file (CLAUDE.md / AGENTS.md)
    # This ensures the agent loads harness-manager immediately on startup.
    entry_file = root / ("CLAUDE.md" if agent == "claude" else "AGENTS.md")
    if entry_file.exists():
        content = entry_file.read_text(encoding="utf-8")
        # Detect language from the file content
        has_cn = any("\u4e00" <= c <= "\u9fff" for c in content[:500])
        bootstrap_cn = "4. **立即加载 `harness-manager` 角色**：使用 Skill 工具调用 `harness-install`，由 harness-manager 接管后续路由"
        bootstrap_en = '4. **Immediately load the `harness-manager` role**: use the Skill tool to invoke `harness-install`, letting harness-manager take over routing.'
        bootstrap = bootstrap_cn if has_cn else bootstrap_en
        # Only inject if not already present
        if "harness-manager" not in content and "harness-install" not in content:
            # Find the "3. Read .workflow/state/runtime.yaml" line and insert bootstrap after it
            marker = "3. Read `.workflow/state/runtime.yaml`." if not has_cn else "3. 读取 `.workflow/state/runtime.yaml`"
            if marker in content:
                lines = content.splitlines(keepends=True)
                new_lines: list[str] = []
                for line in lines:
                    new_lines.append(line)
                    if marker in line:
                        new_lines.append(bootstrap + "\n")
                content = "".join(new_lines)
                entry_file.write_text(content, encoding="utf-8")
                print(f"Bootstrap written to {entry_file.name}")
            else:
                print(f"Warning: could not find runtime.yaml marker in {entry_file.name}")
        else:
            print(f"Bootstrap already present in {entry_file.name}")

    return 0


def scan_project(root: Path) -> int:
    """Scan project characteristics for skill adaptation.

    Args:
        root: Repository root

    Returns:
        0 on success
    """
    print("## 项目适配报告\n")

    # Tech stack detection
    tech_stack: list[str] = []
    build_tools: list[str] = []

    indicators = {
        "Node.js/TypeScript": ["package.json", "package-lock.json"],
        "Go": ["go.mod", "go.sum"],
        "Java/Maven": ["pom.xml"],
        "Rust": ["Cargo.toml", "Cargo.lock"],
        "Python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "C#/.NET": ["*.csproj", "*.sln"],
    }

    for stack, files in indicators.items():
        for pattern in files:
            if "*" in pattern:
                if list(root.glob(pattern)):
                    tech_stack.append(stack)
                    break
            elif (root / pattern).exists():
                tech_stack.append(stack)
                break

    print("### 技术栈")
    if tech_stack:
        for t in tech_stack:
            print(f"- {t}")
    else:
        print("- 未检测到已知技术栈")

    # Directory structure
    print("\n### 目录结构")
    dir_indicators = {
        "源码目录": ["src", "lib", "app"],
        "测试目录": ["tests", "test", "spec"],
        "文档目录": ["docs", "doc"],
        "CI/CD 配置": [".github", ".gitlab-ci.yml", "Jenkinsfile"],
        "辅助脚本": ["scripts", "tools"],
    }

    found_dirs: dict[str, list[str]] = {}
    for category, dirs in dir_indicators.items():
        found = []
        for d in dirs:
            if (root / d).exists():
                found.append(d)
        if found:
            found_dirs[category] = found

    for category, dirs in found_dirs.items():
        print(f"- {category}: {', '.join(dirs)}")

    if not found_dirs:
        print("- 未检测到标准目录结构")

    # Existing standards
    print("\n### 已有规范")
    standards = {
        "工作流规范": ".workflow/context/index.md",
        "开发规范": ".workflow/context/team/development-standards.md",
        "Agent 配置": ".claude/skills",
    }

    for name, path in standards.items():
        status = "存在" if (root / path).exists() else "不存在"
        print(f"- {name}: {status}")

    # Suggestions
    print("\n### 建议")
    if tech_stack:
        print(f"- 基于检测到的技术栈 ({', '.join(tech_stack)})，建议启用相关工具集成")
    else:
        print("- 建议在项目中添加技术栈标志性文件以便工具自动检测")
        print("  (如 package.json, go.mod, pom.xml 等)")

    if not found_dirs.get("开发规范"):
        print("- 建议添加 development-standards.md 定义团队开发规范")

    return 0
