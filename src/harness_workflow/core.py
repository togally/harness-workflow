from __future__ import annotations

import hashlib
import json
import re
import shutil
import unicodedata
from datetime import date
from importlib.resources import files
from pathlib import Path

from harness_workflow import __version__


PACKAGE_ROOT = files("harness_workflow")
SKILL_ROOT = PACKAGE_ROOT.joinpath("assets", "skill")
TEMPLATE_ROOT = SKILL_ROOT.joinpath("assets", "templates")
HARNESS_DIR = Path(".codex") / "harness"
MANAGED_STATE_PATH = HARNESS_DIR / "managed-files.json"
CONFIG_PATH = HARNESS_DIR / "config.json"
WORKFLOW_RUNTIME_PATH = Path("docs") / "context" / "rules" / "workflow-runtime.yaml"

DEFAULT_LANGUAGE = "english"
DEFAULT_CONFIG = {"language": DEFAULT_LANGUAGE, "current_version": ""}
LANGUAGE_ALIASES = {
    "english": "english",
    "en": "english",
    "cn": "cn",
    "zh": "cn",
    "chinese": "cn",
}
DEFAULT_RUNTIME = {
    "current_version": "",
    "executing_version": "",
    "mode": "normal",
    "conversation_mode": "open",
    "locked_version": "",
    "locked_stage": "",
    "locked_artifact_kind": "",
    "locked_artifact_id": "",
    "current_regression": "",
    "active_versions": {},
}
DEFAULT_VERSION_META = {
    "id": "",
    "title": "",
    "status": "draft",
    "stage": "idle",
    "current_task": "",
    "next_action": "",
    "current_artifact_kind": "",
    "current_artifact_id": "",
    "suggested_skill": "",
    "assistant_prompt": "",
    "approval_required": False,
    "completed_tasks": [],
    "pending_tasks": [],
    "requirement_ids": [],
    "change_ids": [],
    "regression_ids": [],
    "current_regression": "",
    "regression_status": "",
}
WORKFLOW_SEQUENCE = [
    "requirement_review",
    "changes_review",
    "plan_review",
    "ready_for_execution",
    "executing",
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
    {"name": "harness-version", "cli": "harness version", "hint": "<name>"},
    {"name": "harness-active", "cli": "harness active", "hint": "<version>"},
    {"name": "harness-use", "cli": "harness use", "hint": "<version>"},
    {"name": "harness-enter", "cli": "harness enter", "hint": ""},
    {"name": "harness-exit", "cli": "harness exit", "hint": ""},
    {"name": "harness-status", "cli": "harness status", "hint": ""},
    {"name": "harness-requirement", "cli": "harness requirement", "hint": "<title>"},
    {"name": "harness-change", "cli": "harness change", "hint": "<title>"},
    {"name": "harness-plan", "cli": "harness plan", "hint": "<change>"},
    {"name": "harness-next", "cli": "harness next", "hint": "[--execute]"},
    {"name": "harness-ff", "cli": "harness ff", "hint": ""},
    {"name": "harness-regression", "cli": "harness regression", "hint": "<issue>|--confirm|--change <title>"},
    {"name": "harness-archive", "cli": "harness archive", "hint": "<requirement>"},
    {"name": "harness-rename", "cli": "harness rename", "hint": "<kind> <old> <new>"},
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
                "执行前请先：",
                "",
                "1. 读取 `docs/context/rules/workflow-runtime.yaml`",
                "2. 根据 `current_version` 读取对应 version 的 `meta.yaml`",
                "3. 继续读取：",
                "   - `docs/context/rules/development-flow.md`",
                "   - `docs/context/rules/agent-workflow.md`",
                "   - `docs/context/rules/risk-rules.md`",
                "   - `docs/context/experience/index.md`",
                "4. 优先遵循根目录 `AGENTS.md`",
                "5. 如果存在 `.qoder/skills/harness/SKILL.md` 或 `.claude/skills/harness/SKILL.md`，按主 Harness skill 执行",
                "",
                "执行要求：",
                "",
                f"- 优先围绕 `{cli_command}` 的语义推进当前任务",
                "- 不要绕过 workflow 手工推进 requirement / change / plan / execution",
                "- 如果 workflow 状态缺失或冲突，停止并提示运行 `harness active \"<version>\"`",
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
                "Before acting:",
                "",
                "1. Read `docs/context/rules/workflow-runtime.yaml`",
                "2. Use `current_version` to read the active version `meta.yaml`",
                "3. Then read:",
                "   - `docs/context/rules/development-flow.md`",
                "   - `docs/context/rules/agent-workflow.md`",
                "   - `docs/context/rules/risk-rules.md`",
                "   - `docs/context/experience/index.md`",
                "4. Prefer the root `AGENTS.md`",
                "5. If `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill",
                "",
                "Execution rules:",
                "",
                f"- center the task around `{cli_command}`",
                "- do not bypass the workflow with manual requirement / change / plan / execution steps",
                "- if workflow state is missing or inconsistent, stop and tell the user to run `harness active \"<version>\"`",
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
                "执行前：",
                "",
                "1. 先读取 `docs/context/rules/workflow-runtime.yaml`",
                "2. 根据 `current_version` 读取对应 version 的 `meta.yaml`",
                "3. 再读取根目录 `AGENTS.md` 和主 harness skill：`.codex/skills/harness/SKILL.md`",
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
                "Before acting:",
                "",
                "1. Read `docs/context/rules/workflow-runtime.yaml`",
                "2. Use `current_version` to read the active version `meta.yaml`",
                "3. Then read the root `AGENTS.md` and the main harness skill at `.codex/skills/harness/SKILL.md`",
                "",
                "Rules:",
                "",
                f"- treat `{cli_command}` as the primary action",
                "- do not improvise a parallel workflow",
                "- if state is missing or inconsistent, stop and tell the user to run `harness active \"<version>\"`",
                "- if the global `harness` CLI is unavailable, fall back to `.codex/skills/harness/scripts/harness.py`",
            ]
        )
        body.extend(command_specific_guidance(command_name, language))
    return "\n".join(body) + "\n"


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
    return [
        root / ".codex" / "skills" / "harness",
        root / ".claude" / "skills" / "harness",
        root / ".qoder" / "skills" / "harness",
    ]


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    config["current_version"] = config.get("current_version", "").strip()
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


def load_runtime(root: Path) -> dict[str, object]:
    path = root / WORKFLOW_RUNTIME_PATH
    if not path.exists():
        return dict(DEFAULT_RUNTIME)
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_RUNTIME)
    payload.update(data)
    if not isinstance(payload.get("active_versions"), dict):
        payload["active_versions"] = {}
    return payload


def save_runtime(root: Path, runtime: dict[str, object]) -> None:
    path = root / WORKFLOW_RUNTIME_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_RUNTIME)
    payload.update(runtime)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    return [
        root / "docs" / "context" / "team",
        root / "docs" / "context" / "project",
        root / "docs" / "context" / "experience",
        root / "docs" / "context" / "rules",
        root / "docs" / "versions" / "active",
        root / "docs" / "versions" / "archive",
        root / "docs" / "decisions",
        root / "docs" / "runbooks",
        root / "docs" / "templates",
        root / "docs" / "memory",
        root / "tools",
        root / HARNESS_DIR,
    ]


def _managed_file_contents(root: Path, language: str, include_agents: bool, include_claude: bool) -> dict[str, str]:
    repo_name = root.name
    managed = {
        "docs/README.md": render_template("docs-README.md.tmpl", repo_name, language),
        "docs/memory/constitution.md": render_template("constitution.md.tmpl", repo_name, language),
        "docs/context/experience/index.md": render_template("experience-index.md.tmpl", repo_name, language),
        "docs/context/rules/agent-workflow.md": render_template("agent-workflow.md.tmpl", repo_name, language),
        "docs/context/rules/development-flow.md": render_template("development-flow.md.tmpl", repo_name, language),
        "docs/context/rules/risk-rules.md": render_template("risk-rules.md.tmpl", repo_name, language),
        "docs/context/project/project-overview.md": render_template("project-overview.md.tmpl", repo_name, language),
        "docs/context/team/development-standards.md": render_template("development-standards.md.tmpl", repo_name, language),
        "docs/templates/requirement.md": render_template("requirement.md.tmpl", repo_name, language),
        "docs/templates/requirement-completion.md": render_template("requirement-completion.md.tmpl", repo_name, language),
        "docs/templates/requirement-changes.md": render_template("requirement-changes.md.tmpl", repo_name, language),
        "docs/templates/change.md": render_template("change.md.tmpl", repo_name, language),
        "docs/templates/change-requirement.md": render_template("change-requirement.md.tmpl", repo_name, language),
        "docs/templates/change-design.md": render_template("change-design.md.tmpl", repo_name, language),
        "docs/templates/change-plan.md": render_template("change-plan.md.tmpl", repo_name, language),
        "docs/templates/change-acceptance.md": render_template("change-acceptance.md.tmpl", repo_name, language),
        "docs/templates/regression-required-inputs.md": render_template("regression-required-inputs.md.tmpl", repo_name, language),
        "docs/templates/session-memory.md": render_template("session-memory.md.tmpl", repo_name, language),
        "docs/templates/regression.md": render_template("regression.md.tmpl", repo_name, language),
        "docs/templates/regression-analysis.md": render_template("regression-analysis.md.tmpl", repo_name, language),
        "docs/templates/regression-decision.md": render_template("regression-decision.md.tmpl", repo_name, language),
        "docs/templates/regression-meta.yaml": render_template("regression-meta.yaml.tmpl", repo_name, language),
        "docs/templates/version-readme.md": render_template("version-readme.md.tmpl", repo_name, language),
        "docs/templates/version-memory.md": render_template("version-memory.md.tmpl", repo_name, language),
        ".qoder/commands/harness.md": render_template("qoder-command.md.tmpl", repo_name, language),
        ".qoder/rules/harness-workflow.md": render_template("qoder-rule.md.tmpl", repo_name, language),
        "tools/lint_harness_repo.py": SKILL_ROOT.joinpath("scripts", "lint_harness_repo.py").read_text(encoding="utf-8"),
    }
    if include_agents:
        managed["AGENTS.md"] = render_template("AGENTS.md.tmpl", repo_name, language)
    if include_claude:
        managed["CLAUDE.md"] = render_template("CLAUDE.md.tmpl", repo_name, language)
    for command in COMMAND_DEFINITIONS:
        markdown = render_agent_command(command["name"], command["cli"], command["hint"], language)
        managed[f".qoder/commands/{command['name']}.md"] = markdown
        managed[f".claude/commands/{command['name']}.md"] = markdown
        managed[f".codex/skills/{command['name']}/SKILL.md"] = render_codex_command_skill(
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
    required = [root / "docs", root / "docs" / "context", root / "docs" / "versions" / "active"]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"Harness workspace is missing. Run `harness install` or `harness init` first. Missing: {', '.join(missing)}")
    return ensure_config(root)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return slug


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


def resolve_version_layout(root: Path, version_id: str, language: str) -> dict[str, Path]:
    spec = language_spec(language)
    version_dir = root / "docs" / "versions" / "active" / version_id
    return {
        "version_dir": version_dir,
        "requirements_dir": version_dir / spec["requirements_dir"],
        "changes_dir": version_dir / spec["changes_dir"],
        "plans_dir": version_dir / spec["plans_dir"],
        "regressions_dir": version_dir / spec["regressions_dir"],
        "archive_dir": version_dir / spec["archive_dir"],
        "version_memory": version_dir / spec["version_memory"],
    }


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


def fallback_stage_for_artifacts(meta: dict[str, object], requirement_ids: list[str], change_ids: list[str]) -> dict[str, object]:
    payload = dict(meta)
    if change_ids:
        focus_change = change_ids[-1]
        payload.update(
            {
                "status": "in_progress",
                "stage": "changes_review",
                "current_task": f"Review change {focus_change}",
                "next_action": "Discuss the change list and confirm the active change, then run `harness next`.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
                "suggested_skill": "brainstorming",
                "assistant_prompt": f"Use brainstorming to refine change {focus_change}, fill the change document, and stop for human review.",
                "approval_required": True,
            }
        )
        return payload
    if requirement_ids:
        focus_requirement = requirement_ids[-1]
        payload.update(
            {
                "status": "in_progress",
            "stage": "requirement_review",
            "current_task": f"Review requirement {focus_requirement}",
            "next_action": "Discuss and confirm the requirement, then run `harness next` to move into change design.",
            "current_artifact_kind": "requirement",
            "current_artifact_id": focus_requirement,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to draft and refine requirement {focus_requirement} in its document. Treat any implementation-oriented prompt as discussion input only. Do not write production code, modify source files, or start implementation during requirement_review. Stop for human review before any change design or coding.",
            "approval_required": True,
        }
        )
        return payload
    payload.update(
        {
            "status": "in_progress",
            "stage": "idle",
            "current_task": "Create or review the first requirement",
            "next_action": "Run `harness requirement <title>` to begin requirement drafting.",
            "current_artifact_kind": "",
            "current_artifact_id": "",
            "suggested_skill": "",
            "assistant_prompt": "",
            "approval_required": False,
        }
    )
    return payload


def list_existing_versions(root: Path) -> list[str]:
    active_dir = root / "docs" / "versions" / "active"
    if not active_dir.exists():
        return []
    return sorted(path.name for path in active_dir.iterdir() if path.is_dir())


def active_version_instruction(root: Path, version_id: str = "") -> str:
    if version_id:
        return f'Run `harness active "{version_id}"`.'
    version_ids = list_existing_versions(root)
    if len(version_ids) == 1:
        return f'Run `harness active "{version_ids[0]}"`.'
    if version_ids:
        choices = ", ".join(f"`{item}`" for item in version_ids)
        return f"Run `harness active <version>` for one of: {choices}."
    return "Run `harness version <name>` first."


def workflow_blockers(root: Path, config: dict[str, str], runtime: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    version_ids = list_existing_versions(root)
    if not version_ids:
        return blockers

    runtime_version = str(runtime.get("current_version", "")).strip()
    config_version = str(config.get("current_version", "")).strip()

    if runtime_version != config_version:
        if runtime_version and config_version:
            blockers.append(
                f"workflow runtime points to `{runtime_version}` but harness config points to `{config_version}`. "
                f"{active_version_instruction(root)}"
            )
        else:
            missing_side = "workflow runtime" if not runtime_version else "harness config"
            selected = config_version or runtime_version
            blockers.append(
                f"{missing_side} is missing the active version while `{selected}` exists elsewhere. "
                f"{active_version_instruction(root, selected)}"
            )

    effective_version = runtime_version or config_version
    if not effective_version:
        blockers.append(f"workflow routing has no active version. {active_version_instruction(root)}")
        return blockers

    if effective_version not in version_ids:
        blockers.append(
            f"active version `{effective_version}` does not exist under `docs/versions/active/`. "
            f"{active_version_instruction(root)}"
        )
        return blockers

    if not version_meta_path(root, effective_version).exists():
        blockers.append(
            f"active version `{effective_version}` is missing `meta.yaml`. Restore or recreate the version, then "
            f"{active_version_instruction(root, effective_version)}"
        )
    return blockers


def require_active_version_id(root: Path, config: dict[str, str], runtime: dict[str, object] | None = None) -> str:
    runtime_payload = dict(runtime or load_runtime(root))
    blockers = workflow_blockers(root, config, runtime_payload)
    if blockers:
        raise SystemExit(f"Workflow is blocked: {blockers[0]}")
    return str(runtime_payload.get("current_version", "") or config.get("current_version", "")).strip()


def current_version_layout(root: Path, config: dict[str, str]) -> dict[str, Path]:
    current_version = require_active_version_id(root, config)
    return resolve_version_layout(root, current_version, config["language"])


def version_meta_path(root: Path, version_id: str) -> Path:
    return root / "docs" / "versions" / "active" / version_id / "meta.yaml"


def load_version_meta(root: Path, version_id: str) -> dict[str, object]:
    path = version_meta_path(root, version_id)
    if not path.exists():
        payload = dict(DEFAULT_VERSION_META)
        payload["id"] = version_id
        payload["title"] = version_id
        return payload
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = dict(DEFAULT_VERSION_META)
    payload.update(data)
    return payload


def save_version_meta(root: Path, version_id: str, meta: dict[str, object]) -> None:
    path = version_meta_path(root, version_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(DEFAULT_VERSION_META)
    payload.update(meta)
    payload["id"] = version_id
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_workflow_state(root: Path) -> tuple[dict[str, str], dict[str, object]]:
    config = ensure_harness_root(root)
    runtime = load_runtime(root)
    save_runtime(root, runtime)
    return config, runtime


def sync_runtime_version(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object] | None = None) -> dict[str, object]:
    runtime_payload = dict(runtime or load_runtime(root))
    active_versions = dict(runtime_payload.get("active_versions", {}))
    active_versions[version_id] = {
        "status": str(meta.get("status", "draft")),
        "stage": str(meta.get("stage", "idle")),
        "current_task": str(meta.get("current_task", "")),
        "next_action": str(meta.get("next_action", "")),
        "current_artifact_kind": str(meta.get("current_artifact_kind", "")),
        "current_artifact_id": str(meta.get("current_artifact_id", "")),
        "suggested_skill": str(meta.get("suggested_skill", "")),
        "approval_required": bool(meta.get("approval_required", False)),
        "current_regression": str(meta.get("current_regression", "")),
        "regression_status": str(meta.get("regression_status", "")),
    }
    runtime_payload["active_versions"] = active_versions
    return runtime_payload


def persist_workflow_state(root: Path, version_id: str, meta: dict[str, object], runtime: dict[str, object]) -> None:
    save_version_meta(root, version_id, meta)
    runtime["current_version"] = version_id
    save_runtime(root, sync_runtime_version(root, version_id, meta, runtime))


def regression_workspace_dir(root: Path, version_id: str, language: str, regression_id: str) -> Path:
    return resolve_version_layout(root, version_id, language)["regressions_dir"] / regression_id


def set_regression_mode(runtime: dict[str, object], regression_id: str = "") -> dict[str, object]:
    payload = dict(runtime)
    payload["mode"] = "regression" if regression_id else "normal"
    payload["current_regression"] = regression_id
    return payload


def set_conversation_mode(
    runtime: dict[str, object],
    *,
    conversation_mode: str,
    version_id: str = "",
    meta: dict[str, object] | None = None,
) -> dict[str, object]:
    payload = dict(runtime)
    payload["conversation_mode"] = conversation_mode
    if conversation_mode != "harness":
        payload["locked_version"] = ""
        payload["locked_stage"] = ""
        payload["locked_artifact_kind"] = ""
        payload["locked_artifact_id"] = ""
        return payload
    payload["locked_version"] = version_id
    payload["locked_stage"] = str((meta or {}).get("stage", ""))
    payload["locked_artifact_kind"] = str((meta or {}).get("current_artifact_kind", ""))
    payload["locked_artifact_id"] = str((meta or {}).get("current_artifact_id", ""))
    return payload


def enter_harness_mode(root: Path, runtime: dict[str, object], version_id: str = "", meta: dict[str, object] | None = None) -> dict[str, object]:
    selected_version = version_id.strip()
    selected_meta = meta
    if selected_version and selected_meta is None and version_meta_path(root, selected_version).exists():
        selected_meta = load_version_meta(root, selected_version)
    return set_conversation_mode(runtime, conversation_mode="harness", version_id=selected_version, meta=selected_meta)


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
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan. Keep documents and verification in sync while executing.",
                "approval_required": False,
            }
        )
        return payload

    if stage == "executing":
        payload.update(
            {
                "stage": "done",
                "status": "done",
                "current_task": "Execution finished. Summarize and verify outcomes",
                "next_action": "Verify `mvn compile` for each completed change and successful project startup for the completed requirement before closing. If either check fails, start `harness regression \"<issue>\"`.",
                "suggested_skill": "verification-before-completion",
                "assistant_prompt": "Run final verification. Each completed change must include `mvn compile`. Completed requirement work must include successful project startup validation. If compilation or startup fails, stop and start `harness regression \"<issue>\"`. If user input is needed, fill the related change `regression/required-inputs.md` template and wait for the human response.",
                "approval_required": False,
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
    return None


def resolve_change_reference(changes_dir: Path, reference: str, language: str) -> Path | None:
    direct = changes_dir / reference
    if direct.exists():
        return direct
    derived = changes_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
    return None


def resolve_regression_reference(regressions_dir: Path, reference: str, language: str) -> Path | None:
    direct = regressions_dir / reference
    if direct.exists():
        return direct
    derived = regressions_dir / resolve_artifact_id(reference, language)
    if derived.exists():
        return derived
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


def rebuild_runtime_index(root: Path, runtime: dict[str, object]) -> dict[str, object]:
    payload = dict(runtime)
    payload["active_versions"] = {}
    for version_id in list_existing_versions(root):
        if version_meta_path(root, version_id).exists():
            payload = sync_runtime_version(root, version_id, load_version_meta(root, version_id), payload)
    return payload


def repair_identifier_drift(root: Path, config: dict[str, str], runtime: dict[str, object], check: bool) -> tuple[dict[str, str], dict[str, object], list[str]]:
    actions: list[str] = []
    version_map: dict[str, str] = {}
    versions_root = root / "docs" / "versions" / "active"
    version_ids = list_existing_versions(root)

    for field in ("current_version",):
        current_value = str(config.get(field, "")).strip()
        if current_value and current_value not in version_ids and version_ids:
            fallback = next((candidate for candidate in runtime.get("active_versions", {}) if candidate in version_ids), version_ids[0])
            actions.append(f"{'would roll back' if check else 'rolled back'} active version {current_value} -> {fallback}")
            if not check:
                config[field] = fallback
    for field in ("current_version", "executing_version"):
        current_value = str(runtime.get(field, "")).strip()
        if current_value and current_value not in version_ids:
            fallback = ""
            if field == "current_version" and version_ids:
                fallback = next((candidate for candidate in runtime.get("active_versions", {}) if candidate in version_ids), version_ids[0])
            actions.append(
                f"{'would roll back' if check else 'rolled back'} runtime {field} {current_value} -> {fallback or '(none)'}"
            )
            if not check:
                runtime[field] = fallback

    for version_dir in sorted(path for path in versions_root.iterdir() if path.is_dir()):
        meta_path = version_dir / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = load_version_meta(root, version_dir.name)
        old_id = str(meta.get("id", "")).strip()
        if old_id and old_id != version_dir.name:
            version_map[old_id] = version_dir.name
            actions.append(f"{'would repair' if check else 'repaired'} version id {old_id} -> {version_dir.name}")
            if not check:
                if str(meta.get("title", "")) == old_id:
                    meta["title"] = version_dir.name
                meta["id"] = version_dir.name
                save_version_meta(root, version_dir.name, meta)

    if version_map:
        current_version = str(config.get("current_version", ""))
        executing_version = str(runtime.get("executing_version", ""))
        if current_version in version_map:
            config["current_version"] = version_map[current_version]
        if str(runtime.get("current_version", "")) in version_map:
            runtime["current_version"] = version_map[str(runtime.get("current_version", ""))]
        if executing_version in version_map:
            runtime["executing_version"] = version_map[executing_version]

    for version_dir in sorted(path for path in versions_root.iterdir() if path.is_dir()):
        if not (version_dir / "meta.yaml").exists():
            continue
        version_id = version_dir.name
        layout = resolve_version_layout(root, version_id, config["language"])
        requirement_map: dict[str, str] = {}
        change_map: dict[str, str] = {}

        if layout["requirements_dir"].exists():
            for requirement_dir in sorted(path for path in layout["requirements_dir"].iterdir() if path.is_dir()):
                meta_path = requirement_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                old_id = meta.get("id", "").strip()
                if old_id and old_id != requirement_dir.name:
                    requirement_map[old_id] = requirement_dir.name
                    actions.append(f"{'would repair' if check else 'repaired'} requirement id {old_id} -> {requirement_dir.name}")
                    if not check:
                        meta["id"] = requirement_dir.name
                        save_item_meta(meta_path, meta)

        if layout["changes_dir"].exists():
            for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
                meta_path = change_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                old_id = meta.get("id", "").strip()
                if old_id and old_id != change_dir.name:
                    change_map[old_id] = change_dir.name
                    actions.append(f"{'would repair' if check else 'repaired'} change id {old_id} -> {change_dir.name}")
                    if not check:
                        meta["id"] = change_dir.name
                        save_item_meta(meta_path, meta)

        if requirement_map or change_map:
            version_meta = load_version_meta(root, version_id)
            version_meta["requirement_ids"] = remap_identifier_list(list(version_meta.get("requirement_ids", [])), requirement_map)
            version_meta["change_ids"] = remap_identifier_list(list(version_meta.get("change_ids", [])), change_map)
            if str(version_meta.get("current_artifact_kind", "")) == "requirement":
                version_meta["current_artifact_id"] = requirement_map.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
            if str(version_meta.get("current_artifact_kind", "")) in {"change", "plan"}:
                version_meta["current_artifact_id"] = change_map.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
            version_meta = remap_meta_strings(version_meta, {**requirement_map, **change_map})
            if not check:
                save_version_meta(root, version_id, version_meta)

        actual_requirement_ids = []
        if layout["requirements_dir"].exists():
            actual_requirement_ids = sorted(path.name for path in layout["requirements_dir"].iterdir() if path.is_dir() and (path / "meta.yaml").exists())
        actual_change_ids = []
        if layout["changes_dir"].exists():
            actual_change_ids = sorted(path.name for path in layout["changes_dir"].iterdir() if path.is_dir() and (path / "meta.yaml").exists())
        actual_regression_ids = []
        if layout["regressions_dir"].exists():
            actual_regression_ids = sorted(path.name for path in layout["regressions_dir"].iterdir() if path.is_dir() and (path / "meta.yaml").exists())

        if layout["changes_dir"].exists():
            for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
                meta_path = change_dir / "meta.yaml"
                if not meta_path.exists():
                    continue
                meta = load_item_meta(meta_path)
                requirement_ref = meta.get("requirement", "").strip()
                if requirement_ref in requirement_map:
                    actions.append(
                        f"{'would repair' if check else 'repaired'} change requirement link {requirement_ref} -> {requirement_map[requirement_ref]}"
                    )
                    if not check:
                        meta["requirement"] = requirement_map[requirement_ref]
                        save_item_meta(meta_path, meta)
                        replace_in_file(change_dir / "change.md", {requirement_ref: requirement_map[requirement_ref]})
                elif requirement_ref and requirement_ref not in actual_requirement_ids:
                    actions.append(
                        f"{'would clear' if check else 'cleared'} missing requirement link {requirement_ref} from change {change_dir.name}"
                    )
                    if not check:
                        meta["requirement"] = "None"
                        save_item_meta(meta_path, meta)
                        replace_in_file(change_dir / "change.md", {requirement_ref: "None"})

        if change_map and layout["requirements_dir"].exists():
            for requirement_dir in sorted(path for path in layout["requirements_dir"].iterdir() if path.is_dir()):
                replace_in_file(requirement_dir / "changes.md", change_map)

        version_meta = load_version_meta(root, version_id)
        tracked_requirements = [item for item in remap_identifier_list(list(version_meta.get("requirement_ids", [])), requirement_map) if item in actual_requirement_ids]
        tracked_changes = [item for item in remap_identifier_list(list(version_meta.get("change_ids", [])), change_map) if item in actual_change_ids]
        tracked_regressions = [str(item) for item in version_meta.get("regression_ids", []) if str(item) in actual_regression_ids]
        if tracked_requirements != list(version_meta.get("requirement_ids", [])) or tracked_changes != list(version_meta.get("change_ids", [])):
            actions.append(f"{'would reconcile' if check else 'reconciled'} deleted requirement/change references for {version_id}")
            version_meta["requirement_ids"] = tracked_requirements
            version_meta["change_ids"] = tracked_changes
        if tracked_regressions != [str(item) for item in version_meta.get("regression_ids", [])]:
            actions.append(f"{'would reconcile' if check else 'reconciled'} deleted regression references for {version_id}")
            version_meta["regression_ids"] = tracked_regressions
        if str(version_meta.get("current_regression", "")) and str(version_meta.get("current_regression", "")) not in actual_regression_ids:
            actions.append(f"{'would clear' if check else 'cleared'} missing current regression for {version_id}")
            version_meta["current_regression"] = ""
            if not tracked_regressions:
                version_meta["regression_status"] = ""
            if not check and str(runtime.get("current_regression", "")) not in actual_regression_ids:
                runtime = set_regression_mode(runtime, "")

        current_kind = str(version_meta.get("current_artifact_kind", ""))
        current_id = str(version_meta.get("current_artifact_id", ""))
        current_missing = (
            (current_kind == "requirement" and current_id and current_id not in tracked_requirements)
            or (current_kind in {"change", "plan"} and current_id and current_id not in tracked_changes)
            or (str(version_meta.get("stage", "")) in {"plan_review", "ready_for_execution", "executing", "done"} and not tracked_changes)
            or (not tracked_requirements and not tracked_changes and str(version_meta.get("stage", "")) != "idle")
        )
        if current_missing:
            actions.append(f"{'would roll back' if check else 'rolled back'} workflow state for {version_id} after deleted artifacts")
            version_meta = fallback_stage_for_artifacts(version_meta, tracked_requirements, tracked_changes)

        if not check:
            save_version_meta(root, version_id, version_meta)

    if not check:
        runtime = rebuild_runtime_index(root, runtime)
    return config, runtime, actions


def init_repo(root: Path, write_agents: bool, write_claude: bool) -> int:
    created: list[str] = []
    skipped: list[str] = []
    config = ensure_config(root)
    language = config["language"]
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)
    managed_contents = _managed_file_contents(root, language=language, include_agents=write_agents, include_claude=write_claude)
    managed_state = _load_managed_state(root)
    for relative, content in managed_contents.items():
        write_if_missing(root / relative, content, created, skipped)
    _save_managed_state(root, _refresh_managed_state(root, managed_contents, managed_state))
    if not (root / WORKFLOW_RUNTIME_PATH).exists():
        save_runtime(root, dict(DEFAULT_RUNTIME))
        created.append(str(root / WORKFLOW_RUNTIME_PATH))
    runtime = enter_harness_mode(root, load_runtime(root), str(config.get("current_version", "")).strip())
    save_runtime(root, runtime)

    print("Created files:")
    for path in created:
        print(f"- {path}")
    print("")
    print("Skipped existing files:")
    for path in skipped:
        print(f"- {path}")
    return 0


def install_repo(root: Path, force_skill: bool = False) -> int:
    skill_paths = install_local_skills(root, force=force_skill)
    print("Installed local skills:")
    for skill_path in skill_paths:
        print(f"- {skill_path}")
    return init_repo(root, write_agents=True, write_claude=True)


def update_repo(root: Path, check: bool = False, force_managed: bool = False) -> int:
    config = ensure_harness_root(root)
    language = config["language"]
    runtime = load_runtime(root)
    for directory in _required_dirs(root):
        directory.mkdir(parents=True, exist_ok=True)

    managed_contents = _managed_file_contents(root, language=language, include_agents=True, include_claude=True)
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    actions: list[str] = []

    if check:
        actions.append("would refresh .codex/skills/harness")
        actions.append("would refresh .claude/skills/harness")
        actions.append("would refresh .qoder/skills/harness")
    else:
        install_local_skills(root, force=True)
        actions.append("refreshed .codex/skills/harness")
        actions.append("refreshed .claude/skills/harness")
        actions.append("refreshed .qoder/skills/harness")

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

        if managed_state.get(relative) == current_hash:
            actions.append(f"{'would update' if check else 'updated'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        if force_managed:
            actions.append(f"{'would overwrite modified' if check else 'overwrote modified'} {relative}")
            if not check:
                path.write_text(content, encoding="utf-8")
                refreshed_state[relative] = desired_hash
            continue

        actions.append(f"skipped modified {relative}")

    if not check:
        save_config(root, config)
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))
        if not (root / WORKFLOW_RUNTIME_PATH).exists():
            save_runtime(root, dict(DEFAULT_RUNTIME))
            actions.append("created docs/context/rules/workflow-runtime.yaml")
            runtime = load_runtime(root)

    config, runtime, repair_actions = repair_identifier_drift(root, config, runtime, check)
    actions.extend(repair_actions)
    if not check:
        current_version = str(runtime.get("current_version", "") or config.get("current_version", "")).strip()
        runtime = enter_harness_mode(root, runtime, current_version)
        save_config(root, config)
        save_runtime(root, runtime)

    blockers = workflow_blockers(root, config, runtime)
    for blocker in blockers:
        actions.append(f"workflow action required: {blocker}")

    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")
    if blockers:
        print("")
        print("Workflow is blocked until the active version is explicitly repaired.")
        return 1
    return 0


def set_language(root: Path, language: str) -> int:
    config = ensure_config(root)
    config["language"] = normalize_language(language)
    save_config(root, config)
    runtime = enter_harness_mode(root, load_runtime(root), str(config.get("current_version", "")).strip())
    save_runtime(root, runtime)
    print(f"Language set to {config['language']}")
    print("Run `harness update` if you want managed templates and guides to refresh in the new language.")
    return 0


def create_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip()
    if not version_id:
        raise SystemExit("Version name is required.")
    layout = resolve_version_layout(root, version_id, config["language"])
    repo_name = root.name
    created: list[str] = []
    skipped: list[str] = []

    layout["version_dir"].mkdir(parents=True, exist_ok=True)
    layout["requirements_dir"].mkdir(parents=True, exist_ok=True)
    layout["changes_dir"].mkdir(parents=True, exist_ok=True)
    layout["plans_dir"].mkdir(parents=True, exist_ok=True)
    layout["regressions_dir"].mkdir(parents=True, exist_ok=True)
    layout["archive_dir"].mkdir(parents=True, exist_ok=True)

    replacements = {"VERSION_ID": version_id}
    write_if_missing(layout["version_dir"] / "README.md", render_template("version-readme.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(layout["version_memory"], render_template("version-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "title": version_id,
            "status": "in_progress",
            "stage": meta.get("stage", "idle") or "idle",
            "current_task": meta.get("current_task", "") or "Create or review the first requirement",
            "next_action": meta.get("next_action", "") or "Run `harness requirement <title>` to begin requirement drafting.",
            "suggested_skill": meta.get("suggested_skill", "") or "",
            "assistant_prompt": meta.get("assistant_prompt", "") or "",
            "approval_required": bool(meta.get("approval_required", False)),
        }
    )

    config["current_version"] = version_id
    save_config(root, config)
    runtime["executing_version"] = runtime.get("executing_version", "")
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Active version: {version_id}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_requirement(root: Path, name: str | None, requirement_id: str | None = None, title: str | None = None) -> int:
    config, runtime = ensure_workflow_state(root)
    repo_name = root.name
    requirement_title, resolved_id = resolve_title_and_id(name, requirement_id, title, config["language"])
    layout = current_version_layout(root, config)
    requirement_dir = layout["requirements_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": resolved_id, "TITLE": requirement_title}

    write_if_missing(requirement_dir / "requirement.md", render_template("requirement.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "completion.md", render_template("requirement-completion.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "changes.md", render_template("requirement-changes.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(requirement_dir / "meta.yaml", render_template("requirement-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    requirement_ids = [str(item) for item in meta.get("requirement_ids", [])]
    if resolved_id not in requirement_ids:
        requirement_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "requirement_review",
            "current_task": f"Review requirement {resolved_id}",
            "next_action": "Discuss and confirm the requirement, then run `harness next` to move into change design.",
            "current_artifact_kind": "requirement",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to draft and refine requirement {resolved_id} in its document. Treat any implementation-oriented prompt as discussion input only. Do not write production code, modify source files, or start implementation during requirement_review. Stop for human review before any change design or coding.",
            "approval_required": True,
            "requirement_ids": requirement_ids,
        }
    )
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Requirement workspace: {requirement_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_change(
    root: Path,
    name: str | None,
    change_id: str | None = None,
    title: str | None = None,
    requirement_id: str = "",
) -> int:
    config, runtime = ensure_workflow_state(root)
    repo_name = root.name
    change_title, resolved_id = resolve_title_and_id(name, change_id, title, config["language"])
    layout = current_version_layout(root, config)
    change_dir = layout["changes_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []

    linked_requirement = requirement_id.strip() if requirement_id else ""
    replacements = {"ID": resolved_id, "TITLE": change_title, "REQUIREMENT_ID": linked_requirement or "None"}
    if config["language"] == "cn" and not linked_requirement:
        replacements["REQUIREMENT_ID"] = "未指定"

    write_if_missing(change_dir / "change.md", render_template("change.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "design.md", render_template("change-design.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "acceptance.md", render_template("change-acceptance.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "regression" / "required-inputs.md", render_template("regression-required-inputs.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(change_dir / "meta.yaml", render_template("change-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    if linked_requirement:
        requirement_dir = resolve_requirement_reference(layout["requirements_dir"], linked_requirement, config["language"])
        if requirement_dir:
            append_change_to_requirement(requirement_dir, resolved_id, change_title)
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    change_ids = [str(item) for item in meta.get("change_ids", [])]
    if resolved_id not in change_ids:
        change_ids.append(resolved_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "changes_review" if meta.get("stage") in {"idle", "requirement_review", "changes_review"} else meta.get("stage", "changes_review"),
            "current_task": f"Review change {resolved_id}",
            "next_action": "Discuss the change list and confirm the active change, then run `harness next`.",
            "current_artifact_kind": "change",
            "current_artifact_id": resolved_id,
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to refine change {resolved_id}, fill the change document, and stop for human review.",
            "approval_required": True,
            "change_ids": change_ids,
        }
    )
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Change workspace: {change_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def create_plan(root: Path, change_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    layout = current_version_layout(root, config)
    candidate = layout["changes_dir"] / change_name
    if not candidate.exists():
        candidate = layout["changes_dir"] / resolve_artifact_id(change_name, config["language"])
    if not candidate.exists():
        raise SystemExit(f"Change does not exist: {change_name}")
    version_id = str(config["current_version"])
    meta = load_version_meta(root, version_id)
    meta.update(
        {
            "status": "in_progress",
            "stage": "plan_review",
            "current_task": f"Review plan for {candidate.name}",
            "next_action": "Discuss and confirm the plan, then run `harness next` to reach execution confirmation.",
            "current_artifact_kind": "plan",
            "current_artifact_id": candidate.name,
            "suggested_skill": "writing-plans",
            "assistant_prompt": f"Use writing-plans to expand plan.md for {candidate.name}, then stop for human review.",
            "approval_required": True,
        }
    )
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Plan file: {candidate / 'plan.md'}")
    print("Use writing-plans to expand this file into model-executable development and verification steps.")
    return 0


def create_regression(root: Path, name: str | None, regression_id: str | None = None, title: str | None = None) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = require_active_version_id(root, config, runtime)
    repo_name = root.name
    regression_title, resolved_id = resolve_title_and_id(name, regression_id, title, config["language"])
    layout = resolve_version_layout(root, version_id, config["language"])
    regression_dir = layout["regressions_dir"] / resolved_id
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": resolved_id, "TITLE": regression_title}

    write_if_missing(regression_dir / "regression.md", render_template("regression.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "analysis.md", render_template("regression-analysis.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "decision.md", render_template("regression-decision.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "meta.yaml", render_template("regression-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    meta = load_version_meta(root, version_id)
    regression_ids = [str(item) for item in meta.get("regression_ids", [])]
    if resolved_id not in regression_ids:
        regression_ids.append(resolved_id)
    meta.update(
        {
            "current_regression": resolved_id,
            "regression_status": "analysis",
            "regression_ids": regression_ids,
            "current_task": f"Analyze regression {resolved_id}",
            "next_action": "Confirm whether this is a real problem. Use `harness regression --confirm`, `--reject`, or `--cancel`.",
            "suggested_skill": "brainstorming",
            "assistant_prompt": f"Use brainstorming to analyze regression {resolved_id}, determine whether it is a real issue, discuss with the user, and stop for confirmation before creating new work.",
            "approval_required": True,
        }
    )
    runtime = enter_harness_mode(root, set_regression_mode(runtime, resolved_id), version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)

    print(f"Regression workspace: {regression_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def regression_action(
    root: Path,
    *,
    status_only: bool = False,
    confirm: bool = False,
    reject: bool = False,
    cancel: bool = False,
    change_title: str = "",
    requirement_title: str = "",
) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = require_active_version_id(root, config, runtime)
    meta = load_version_meta(root, version_id)
    regression_id = str(meta.get("current_regression", "") or runtime.get("current_regression", "")).strip()
    if not regression_id:
        raise SystemExit("No active regression. Start one with `harness regression \"<issue>\"` first.")
    regression_dir = regression_workspace_dir(root, version_id, config["language"], regression_id)
    if not regression_dir.exists():
        raise SystemExit(f"Regression does not exist: {regression_id}")

    if status_only:
        print(f"current_regression: {regression_id}")
        print(f"regression_status: {meta.get('regression_status', '') or 'analysis'}")
        print(f"regression_path: {regression_dir}")
        return 0

    chosen = sum(bool(value) for value in [confirm, reject, cancel, bool(change_title), bool(requirement_title)])
    if chosen != 1:
        raise SystemExit("Choose exactly one regression action: --confirm, --reject, --cancel, --change, or --requirement.")

    if confirm:
        meta["regression_status"] = "confirmed"
        meta["current_task"] = f"Regression {regression_id} confirmed. Decide whether to create a requirement update or change."
        meta["next_action"] = "Run `harness regression --change \"<title>\"` or `harness regression --requirement \"<title>\"`."
        update_item_meta(
            regression_dir / "meta.yaml",
            {
                "status": "confirmed",
                "needs_user_input": "false",
                "input_template": "regression/required-inputs.md",
            },
        )
        save_version_meta(root, version_id, meta)
        save_runtime(root, enter_harness_mode(root, set_regression_mode(runtime, regression_id), version_id, meta))
        print(f"Regression confirmed: {regression_id}")
        return 0

    if reject:
        meta["regression_status"] = "rejected"
        meta["current_regression"] = ""
        meta["regression_ids"] = [str(item) for item in meta.get("regression_ids", []) if str(item) != regression_id]
        update_item_meta(regression_dir / "meta.yaml", {"status": "rejected"})
        meta = fallback_stage_for_artifacts(meta, [str(item) for item in meta.get("requirement_ids", [])], [str(item) for item in meta.get("change_ids", [])])
        runtime = enter_harness_mode(root, set_regression_mode(runtime, ""), version_id, meta)
        meta["regression_status"] = ""
        persist_workflow_state(root, version_id, meta, runtime)
        print(f"Regression rejected: {regression_id}")
        return 0

    if cancel:
        meta["regression_status"] = "cancelled"
        meta["current_regression"] = ""
        meta["regression_ids"] = [str(item) for item in meta.get("regression_ids", []) if str(item) != regression_id]
        update_item_meta(regression_dir / "meta.yaml", {"status": "cancelled"})
        meta = fallback_stage_for_artifacts(meta, [str(item) for item in meta.get("requirement_ids", [])], [str(item) for item in meta.get("change_ids", [])])
        runtime = enter_harness_mode(root, set_regression_mode(runtime, ""), version_id, meta)
        meta["regression_status"] = ""
        persist_workflow_state(root, version_id, meta, runtime)
        print(f"Regression cancelled: {regression_id}")
        return 0

    if str(meta.get("regression_status", "")) != "confirmed":
        raise SystemExit("Regression is not confirmed yet. Use `harness regression --confirm` first.")

    meta["current_regression"] = ""
    meta["regression_status"] = ""
    meta["regression_ids"] = [str(item) for item in meta.get("regression_ids", []) if str(item) != regression_id]
    runtime = enter_harness_mode(root, set_regression_mode(runtime, ""), version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)

    if change_title:
        exit_code = create_change(root, change_title)
        linked_change_id = resolve_artifact_id(change_title, config["language"])
        update_item_meta(
            regression_dir / "meta.yaml",
            {
                "status": "converted",
                "linked_change": linked_change_id,
                "linked_requirement": "",
                "needs_user_input": "false",
                "input_template": "regression/required-inputs.md",
            },
        )
        return exit_code
    exit_code = create_requirement(root, requirement_title)
    linked_requirement_id = resolve_artifact_id(requirement_title, config["language"])
    update_item_meta(
        regression_dir / "meta.yaml",
        {
            "status": "converted",
            "linked_change": "",
            "linked_requirement": linked_requirement_id,
            "needs_user_input": "false",
            "input_template": "regression/required-inputs.md",
        },
    )
    return exit_code


def rename_version(root: Path, current_name: str, new_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    old_id = current_name.strip()
    new_id = new_name.strip()
    if not old_id or not new_id:
        raise SystemExit("Both current and new version names are required.")
    old_dir = root / "docs" / "versions" / "active" / old_id
    new_dir = root / "docs" / "versions" / "active" / new_id
    if not old_dir.exists():
        raise SystemExit(f"Version does not exist: {old_id}")
    if new_dir.exists():
        raise SystemExit(f"Target version already exists: {new_id}")

    shutil.move(str(old_dir), str(new_dir))
    meta = load_version_meta(root, new_id)
    meta["id"] = new_id
    meta["title"] = new_id
    meta = remap_meta_strings(meta, {old_id: new_id})
    save_version_meta(root, new_id, meta)

    if str(config.get("current_version", "")) == old_id:
        config["current_version"] = new_id
    if str(runtime.get("current_version", "")) == old_id:
        runtime["current_version"] = new_id
    if str(runtime.get("executing_version", "")) == old_id:
        runtime["executing_version"] = new_id
    save_config(root, config)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Version renamed: {old_id} -> {new_id}")
    return 0


def rename_requirement(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    requirement_dir = resolve_requirement_reference(layout["requirements_dir"], current_name, config["language"])
    if not requirement_dir:
        raise SystemExit(f"Requirement does not exist: {current_name}")

    meta_path = requirement_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path)
    old_id = item_meta.get("id", requirement_dir.name) or requirement_dir.name
    old_title = item_meta.get("title", old_id) or old_id
    new_title, new_id = resolve_title_and_id(new_name, None, None, config["language"])
    target_dir = layout["requirements_dir"] / new_id
    if target_dir.exists():
        raise SystemExit(f"Target requirement already exists: {new_id}")

    shutil.move(str(requirement_dir), str(target_dir))
    item_meta["id"] = new_id
    item_meta["title"] = new_title
    save_item_meta(target_dir / "meta.yaml", item_meta)
    replace_in_file(target_dir / "requirement.md", {old_title: new_title, old_id: new_id})

    if layout["changes_dir"].exists():
        for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
            change_meta_path = change_dir / "meta.yaml"
            if not change_meta_path.exists():
                continue
            change_meta = load_item_meta(change_meta_path)
            if change_meta.get("requirement", "") == old_id:
                change_meta["requirement"] = new_id
                save_item_meta(change_meta_path, change_meta)
                replace_in_file(change_dir / "change.md", {old_id: new_id, old_title: new_title})

    version_meta = load_version_meta(root, version_id)
    version_meta["requirement_ids"] = remap_identifier_list(list(version_meta.get("requirement_ids", [])), {old_id: new_id})
    if str(version_meta.get("current_artifact_kind", "")) == "requirement":
        version_meta["current_artifact_id"] = {old_id: new_id}.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
    version_meta = remap_meta_strings(version_meta, {old_id: new_id, old_title: new_title})
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Requirement renamed: {old_id} -> {new_id}")
    return 0


def rename_change(root: Path, current_name: str, new_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    change_dir = resolve_change_reference(layout["changes_dir"], current_name, config["language"])
    if not change_dir:
        raise SystemExit(f"Change does not exist: {current_name}")

    meta_path = change_dir / "meta.yaml"
    item_meta = load_item_meta(meta_path)
    old_id = item_meta.get("id", change_dir.name) or change_dir.name
    old_title = item_meta.get("title", old_id) or old_id
    new_title, new_id = resolve_title_and_id(new_name, None, None, config["language"])
    target_dir = layout["changes_dir"] / new_id
    if target_dir.exists():
        raise SystemExit(f"Target change already exists: {new_id}")

    shutil.move(str(change_dir), str(target_dir))
    item_meta["id"] = new_id
    item_meta["title"] = new_title
    save_item_meta(target_dir / "meta.yaml", item_meta)
    replace_in_file(target_dir / "change.md", {old_title: new_title, old_id: new_id})

    requirement_ref = item_meta.get("requirement", "").strip()
    if requirement_ref:
        requirement_dir = resolve_requirement_reference(layout["requirements_dir"], requirement_ref, config["language"])
        if requirement_dir:
            replace_in_file(requirement_dir / "changes.md", {old_id: new_id, old_title: new_title})

    version_meta = load_version_meta(root, version_id)
    version_meta["change_ids"] = remap_identifier_list(list(version_meta.get("change_ids", [])), {old_id: new_id})
    if str(version_meta.get("current_artifact_kind", "")) in {"change", "plan"}:
        version_meta["current_artifact_id"] = {old_id: new_id}.get(str(version_meta.get("current_artifact_id", "")), str(version_meta.get("current_artifact_id", "")))
    version_meta = remap_meta_strings(version_meta, {old_id: new_id, old_title: new_title})
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Change renamed: {old_id} -> {new_id}")
    return 0


def archive_requirement(root: Path, requirement_name: str, version_name: str = "") -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip() or require_active_version_id(root, config, runtime)
    layout = resolve_version_layout(root, version_id, config["language"])
    requirement_dir = resolve_requirement_reference(layout["requirements_dir"], requirement_name, config["language"])
    if not requirement_dir:
        raise SystemExit(f"Requirement does not exist: {requirement_name}")

    requirement_id = requirement_dir.name
    archive_root = layout["archive_dir"]
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_requirement_dir = archive_root / requirement_id
    if archive_requirement_dir.exists():
        raise SystemExit(f"Archive target already exists: {archive_requirement_dir}")

    linked_changes: list[Path] = []
    if layout["changes_dir"].exists():
        for change_dir in sorted(path for path in layout["changes_dir"].iterdir() if path.is_dir()):
            change_meta = load_item_meta(change_dir / "meta.yaml")
            if change_meta.get("requirement", "") == requirement_id:
                linked_changes.append(change_dir)

    shutil.move(str(requirement_dir), str(archive_root))
    archived_requirement_dir = archive_root / requirement_id
    archived_changes_dir = archived_requirement_dir / language_spec(config["language"])["changes_dir"]
    archived_changes_dir.mkdir(parents=True, exist_ok=True)
    archived_change_ids: list[str] = []
    for change_dir in linked_changes:
        archived_change_ids.append(change_dir.name)
        shutil.move(str(change_dir), str(archived_changes_dir))

    version_meta = load_version_meta(root, version_id)
    version_meta["requirement_ids"] = [item for item in remap_identifier_list(list(version_meta.get("requirement_ids", [])), {}) if item != requirement_id]
    version_meta["change_ids"] = [item for item in remap_identifier_list(list(version_meta.get("change_ids", [])), {}) if item not in archived_change_ids]
    current_kind = str(version_meta.get("current_artifact_kind", ""))
    current_id = str(version_meta.get("current_artifact_id", ""))
    if (current_kind == "requirement" and current_id == requirement_id) or (
        current_kind in {"change", "plan"} and current_id in archived_change_ids
    ):
        version_meta["current_artifact_kind"] = ""
        version_meta["current_artifact_id"] = ""
        version_meta["current_task"] = "Archived completed work. Select the next active requirement or change."
        version_meta["next_action"] = "Run `harness status` to review remaining active work, or create a new requirement."
    if not version_meta["requirement_ids"] and not version_meta["change_ids"] and str(version_meta.get("stage", "")) not in {"executing", "done"}:
        version_meta["stage"] = "idle"
        version_meta["status"] = "in_progress"
        version_meta["current_task"] = "Create or review the next requirement"
        version_meta["next_action"] = "Run `harness requirement <title>` to begin requirement drafting."
        version_meta["suggested_skill"] = ""
        version_meta["assistant_prompt"] = ""
        version_meta["approval_required"] = False
    save_version_meta(root, version_id, version_meta)
    runtime = rebuild_runtime_index(root, runtime)
    save_runtime(root, runtime)
    print(f"Archived requirement: {requirement_id}")
    print(f"Archive path: {archived_requirement_dir}")
    return 0


def set_active_version(root: Path, version_name: str) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = version_name.strip()
    if not version_meta_path(root, version_id).exists():
        raise SystemExit(f"Version does not exist: {version_id}")
    config["current_version"] = version_id
    save_config(root, config)
    meta = load_version_meta(root, version_id)
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    persist_workflow_state(root, version_id, meta, runtime)
    print(f"Current active version set to {version_id}")
    return 0


def use_version(root: Path, version_name: str) -> int:
    return set_active_version(root, version_name)


def workflow_status(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    current_version = str(runtime.get("current_version", "") or config.get("current_version", ""))
    print(f"current_version: {current_version or '(none)'}")
    print(f"executing_version: {runtime.get('executing_version', '') or '(none)'}")
    print(f"mode: {runtime.get('mode', 'normal')}")
    print(f"conversation_mode: {runtime.get('conversation_mode', 'open')}")
    print(f"locked_version: {runtime.get('locked_version', '') or '(none)'}")
    print(f"locked_stage: {runtime.get('locked_stage', '') or '(none)'}")
    print(f"locked_artifact_kind: {runtime.get('locked_artifact_kind', '') or '(none)'}")
    print(f"locked_artifact_id: {runtime.get('locked_artifact_id', '') or '(none)'}")
    print(f"current_regression: {runtime.get('current_regression', '') or '(none)'}")
    blockers = workflow_blockers(root, config, runtime)
    if blockers:
        print("workflow_blockers:")
        for blocker in blockers:
            print(f"- {blocker}")
    if current_version:
        meta = load_version_meta(root, current_version)
        print(f"stage: {meta.get('stage', 'idle')}")
        print(f"status: {meta.get('status', 'draft')}")
        print(f"current_task: {meta.get('current_task', '') or '(none)'}")
        print(f"next_action: {meta.get('next_action', '') or '(none)'}")
        print(f"current_artifact: {meta.get('current_artifact_kind', '')}:{meta.get('current_artifact_id', '')}".rstrip(":"))
        print(f"regression_status: {meta.get('regression_status', '') or '(none)'}")
        print(f"suggested_skill: {meta.get('suggested_skill', '') or '(none)'}")
        print(f"approval_required: {bool(meta.get('approval_required', False))}")
    return 0


def workflow_next(root: Path, execute: bool = False) -> int:
    config, runtime = ensure_workflow_state(root)
    if str(runtime.get("mode", "normal")) == "regression":
        raise SystemExit("Regression flow is active. Resolve it with `harness regression --confirm`, `--reject`, `--cancel`, `--change`, or `--requirement` first.")
    current_version = require_active_version_id(root, config, runtime)
    meta = load_version_meta(root, current_version)
    meta = apply_stage_transition(meta, execute=execute)
    runtime["executing_version"] = current_version if meta.get("stage") == "executing" else ""
    runtime = enter_harness_mode(root, runtime, current_version, meta)
    persist_workflow_state(root, current_version, meta, runtime)
    print(f"Workflow advanced to {meta['stage']}")
    return 0


def workflow_fast_forward(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    if str(runtime.get("mode", "normal")) == "regression":
        raise SystemExit("Regression flow is active. Resolve it before fast-forwarding the normal workflow.")
    current_version = require_active_version_id(root, config, runtime)
    meta = apply_stage_transition(load_version_meta(root, current_version), fast_forward=True)
    runtime["executing_version"] = ""
    runtime = enter_harness_mode(root, runtime, current_version, meta)
    persist_workflow_state(root, current_version, meta, runtime)
    print("Workflow advanced to ready_for_execution")
    return 0


def enter_workflow(root: Path) -> int:
    config, runtime = ensure_workflow_state(root)
    version_id = str(runtime.get("current_version", "") or config.get("current_version", "")).strip()
    meta = load_version_meta(root, version_id) if version_id and version_meta_path(root, version_id).exists() else None
    runtime = enter_harness_mode(root, runtime, version_id, meta)
    save_runtime(root, runtime)
    if version_id and meta:
        print(f"Entered harness mode: {version_id} / {meta.get('stage', 'idle')}")
    else:
        print("Entered harness mode.")
    return 0


def exit_workflow(root: Path) -> int:
    _config, runtime = ensure_workflow_state(root)
    runtime = exit_harness_mode(runtime)
    save_runtime(root, runtime)
    print("Exited harness mode.")
    return 0
