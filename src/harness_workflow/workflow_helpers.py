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
# bugfix-7 / chg-02：版本号差异化，每次 chg / archive 时 bump；managed-files.json::tool_version
# 跟随写入，install 时对比 mismatch 可触发 full re-sync。
__version__ = "0.2.0"

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
    # req-30（slug 沟通可读性增强：全链路透出 title）/ chg-01：
    # 对 id 字段旁冗余 *_title 缓存，subagent 读一次 runtime 即可拿到 id + title，
    # 无需二次打开 state/requirements/*.yaml。state yaml 为权威源，runtime 为缓存。
    "current_requirement_title": "",
    "stage": "",
    "conversation_mode": "open",
    "locked_requirement": "",
    "locked_requirement_title": "",
    "locked_stage": "",
    "current_regression": "",
    "current_regression_title": "",
    "ff_mode": False,
    "ff_stage_history": [],
    "active_requirements": [],
}
# bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
# 三级布局常量（数字阈值分水岭）已被删除。
# 所有 req / chg / regression 一律走 flow layout（.workflow/flow/requirements/{req-id}-{slug}/），
# 无 fallback 分支，无 legacy 路径创建。
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
    # bugfix-3 根因 B：`.workflow/context/experience/index.md` 是 `_refresh_experience_index`
    # 每次 update 都会活跃再生成的产物，列入 legacy 会触发"搬家 → 重建 → 下次再搬家"循环，
    # `_unique_backup_destination` 产生 index.md-2/-3/... 递增副本堆积。已移除。
    Path(".workflow") / "context" / "experience" / "business",
    Path(".workflow") / "context" / "experience" / "architecture",
    Path(".workflow") / "context" / "experience" / "debug",
    Path(".workflow") / "context" / "experience" / "tool" / "playwright.md",
    Path(".workflow") / "context" / "experience" / "tool" / "mysql-mcp.md",
    Path(".workflow") / "context" / "experience" / "tool" / "nacos-mcp.md",
    Path(".workflow") / "state" / "constitution.md",
    # bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）/
    # chg-1（install_repo cleanup 扩 layout 残留）：
    # `.workflow/flow/artifacts-layout.md` 是 req-39（对人文档家族契约化 + artifacts 扁平化）旧契约文件；
    # req-41（机器型工件回 flow/requirements + 关注点分离 + 废四类 brief（方向 C））将其重命名为
    # `repository-layout.md`，存量项目应在 install 时自动清理旧文件，避免双 layout 共存。
    Path(".workflow") / "flow" / "artifacts-layout.md",
    # bugfix-8 / chg-01：usage-reporter.md 已从 scaffold_v2 中移除；
    # 存量项目若仍有该文件则 install 时兜底清理，防止 mirror 被污染时误判 drift。
    Path(".workflow") / "context" / "roles" / "usage-reporter.md",
]
OPTIONAL_EMPTY_DIRS = [
    Path(".workflow") / "flow" / "archive",
]
# req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance 精简 / 对人文档缩减 / 决策批量化到阶段边界））/
# chg-01（S-A 合并 sub-stage）：
# 将原两个 sub-stage 合并为单一 planning，架构师在一次派发内产出 change.md + plan.md + 变更简报.md。
# 历史兼容：归档 req-02..req-30 的 stage_timestamps 旧字段保留不迁移。
WORKFLOW_SEQUENCE = [
    "analysis",
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
# req-50/chg-01: legacy sequence for req-id < 50 (history archive read-only).
# upstream-fix: workflow_next must accept legacy stages so old-req tests pass.
LEGACY_WORKFLOW_SEQUENCE = [
    "requirement_review",
    "planning",
    "ready_for_execution",
    "executing",
    "testing",
    "acceptance",
    "done",
]
# req-49/trivial track
TRIVIAL_SEQUENCE = [
    "trivial_define",
    "executing",
    "done",
]
VALID_TASK_TYPES = {"req", "requirement", "bugfix", "sug", "suggestion", "trivial"}

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

# bugfix-3（新）问题 2：feedback.jsonl 从 .harness/ 迁到四层 state 归位。
# 所有 record_feedback_event 调用均走此常量，迁移由 update_repo 一次性处理。
FEEDBACK_DIR = Path(".workflow") / "state" / "feedback"
FEEDBACK_LOG = FEEDBACK_DIR / "feedback.jsonl"
# 旧位置保留常量便于 update_repo 做一次性迁移（写入路径已由 FEEDBACK_DIR 管辖）
LEGACY_FEEDBACK_DIR = Path(".harness")
LEGACY_FEEDBACK_LOG = LEGACY_FEEDBACK_DIR / "feedback.jsonl"


# req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））/
# chg-05（install_repo 末尾追加 mirror→live 全量同步）/ chg-06（解锁 _install_self_audit 触发面）：
# scaffold_v2 mirror→live 全量同步 + self-audit 共享白名单（13 条 + A27 missing-log + 3 条 template-rebuild）。
# 白名单 = 不同步（运行时态 / 业务态 / 模板渲染态文件，跨项目独立，不能从 mirror 覆盖回去）。
# 由 `_sync_scaffold_v2_mirror_to_live` 与 `_install_self_audit` 共同消费，避免双份维护。
_SCAFFOLD_V2_MIRROR_WHITELIST: tuple[str, ...] = (
    # 运行时 / 业务态（13 条 + A27）
    "state/sessions",
    "state/requirements",
    "state/bugfixes",
    "state/feedback",
    "state/runtime.yaml",
    "state/runtime-block.yaml",  # bugfix-12（runtime-block.yaml-误判用户野文件-白名单漏配）：raise_harness_block 写运行时阻塞状态，需豁免
    "state/action-log.md",
    "flow/archive",
    "flow/requirements",
    "flow/suggestions",
    "context/backup",
    "context/experience/stage",
    "workflow/archive",
    "tools/index/missing-log.yaml",  # A27 运行时累积，mirror 是模板态空值
    # chg-05 / chg-06 扩展：post-install 系统重建 / 项目专属渲染（mirror 比对会一直 drift，需豁免）
    "context/experience/index.md",   # _refresh_experience_index 按本仓 experience/ 实况重建
    "context/project-profile.md",    # _write_project_profile_if_changed 按 repo 元信息生成
    "CLAUDE.md",                     # render_template 按 repo_name 渲染（与 mirror 模板不同）
    "AGENTS.md",                     # 同 CLAUDE.md
    # bugfix-8 / chg-02：补 3 条业务态目录（工具运行时产出区，不能从 mirror 覆盖）
    "flow/bugfixes",                 # bugfix 流程产出区（harness bugfix 运行时写入）
    "context/experience/regression", # regression 经验沉淀区（harness done 阶段写入）
    "context/experience/risk",       # known-risks 经验沉淀区（harness done 阶段写入）
    # req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）+
    # req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-02（src硬编码main全面去除-branch-aware）：
    # 项目级三类机器型文档承载层（constraints / experience / tools）。chg-01（契约底座-artifacts-project-豁免）
    # 已落 §2.1 / §3 豁免段；req-52 / chg-01（契约层路径迁移-无branch项目级-双轨过渡）OQ-A = D-modified
    # 主路径迁移到 artifacts/project/（无 branch），legacy artifacts/{branch}/project/ 双轨过渡兼容。
    # 白名单匹配语义为 substring（any(white in relative for white in WHITELIST)），下两条覆盖：
    #   - "artifacts/project/" 主路径（无 branch，跟项目走）
    #   - "/project/" substring 兜底捕获 artifacts/<任意 branch>/project/... legacy 路径
    # 共同保证：harness install / update / force-managed 全流程跳过项目级承载层。
    "artifacts/project/",
    "/project/",
)

# req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）/ chg-01：
# harness pad 子命令的 kind / scope 固定枚举（user 不能发明）。
# rule scope 5 类（OQ-Verdicts），experience scope 5 类（沿用 req-51/52 既有），
# tool 不分 scope（直接落 artifacts/project/tools/{slug}.md）。
PAD_KINDS: dict[str, list[str]] = {
    "rule": ["coding", "architecture", "api", "database", "security"],
    "experience": ["roles", "stage", "regression", "risk", "tool"],
    "tool": [],  # 不分 scope
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
    {"name": "harness-install", "cli": "harness install", "hint": "[--agent <cc|codex>] [--force-nested]"},
    {"name": "harness-init", "cli": "harness init", "hint": "[--write-agents|--write-claude]"},
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
    {"name": "harness-playbook-refresh", "cli": "harness playbook-refresh", "hint": ""},
    {"name": "harness-playbook-check", "cli": "harness playbook-check", "hint": ""},
    {"name": "harness-validate", "cli": "harness validate", "hint": "[--contract <name>|--human-docs]"},
    {"name": "harness-trivial", "cli": "harness trivial", "hint": "<title>"},
    {"name": "harness-migrate", "cli": "harness migrate", "hint": "<requirements|bugfix-layout> [--dry-run]"},
    {"name": "harness-tool-search", "cli": "harness tool-search", "hint": "<keywords>"},
    {"name": "harness-tool-rate", "cli": "harness tool-rate", "hint": "<tool> <rating>"},
    {"name": "harness-feedback", "cli": "harness feedback", "hint": "[--reset]"},
    {"name": "harness-pad", "cli": "harness pad", "hint": "<rule|experience|tool|list> [scope] [title]"},
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
    # req-38 / chg-03：YAML null 字面量 → Python None。
    if text.lower() == "null":
        return None
    return text


def load_simple_yaml(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload: dict[str, object] = {}
    current_collection_key = ""
    collection_indent = 0
    # req-38 / chg-03：支持两层嵌套 dict（如 stage_pending_user_action.details.provider）。
    # current_sub_key 追踪当前 dict 值中的子 dict key（第二层 key），sub_indent 记录其缩进。
    current_sub_key = ""
    sub_indent = 0
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
                current_sub_key = ""
                continue
            if ":" in stripped:
                if not isinstance(payload.get(current_collection_key), dict):
                    payload[current_collection_key] = {}
                # 若当前有子 dict key 且 indent 更深，写入子 dict
                if current_sub_key and indent > sub_indent:
                    parent_dict = payload[current_collection_key]
                    if isinstance(parent_dict, dict):
                        if not isinstance(parent_dict.get(current_sub_key), dict):
                            parent_dict[current_sub_key] = {}
                        sk, sv = stripped.split(":", 1)
                        sk = sk.strip()
                        sv = sv.strip()
                        parent_dict[current_sub_key][sk] = _parse_simple_yaml_scalar(sv)  # type: ignore[index]
                        continue
                sub_key, sub_value = stripped.split(":", 1)
                sub_key = sub_key.strip()
                sub_value = sub_value.strip()
                parent_dict2 = payload[current_collection_key]
                if isinstance(parent_dict2, dict):
                    if not sub_value:
                        # 子 key 值为空 → 进入第二层 dict 模式
                        parent_dict2[sub_key] = {}
                        current_sub_key = sub_key
                        sub_indent = indent
                    else:
                        parent_dict2[sub_key] = _parse_simple_yaml_scalar(sub_value)
                        current_sub_key = ""
                continue
        current_collection_key = ""
        current_sub_key = ""
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
        # req-38 / chg-03：None 值输出 YAML null，不转为空字符串。
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, dict):
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
    # bugfix-3 / 缺陷 2（sug-13 复发）扩展：若 operation_type / operation_target
    # 与 current_requirement 前缀**不一致**（如 enter bugfix 后 operation_type 残留
    # "requirement"），强制按 current_requirement 自愈，避免后续 _sync_stage_to_state_yaml
    # 写到错误子目录。
    current_req = str(payload.get("current_requirement", "")).strip()
    operation_type = str(payload.get("operation_type", "")).strip()
    operation_target = str(payload.get("operation_target", "")).strip()

    def _infer_op_type(req_id: str) -> str:
        if req_id.startswith("bugfix-"):
            return "bugfix"
        if req_id.startswith("sug-"):
            return "suggestion"
        if req_id.startswith("trivial-"):
            return "trivial"
        return "requirement"

    if current_req:
        expected_type = _infer_op_type(current_req)
        if not operation_type or operation_type != expected_type:
            payload["operation_type"] = expected_type
        if not operation_target or operation_target != current_req:
            payload["operation_target"] = current_req
    return payload


def _resolve_title_for_id(root: Path, work_item_id: str) -> str:
    """req-30（slug 沟通可读性增强：全链路透出 title）/ chg-01：id → title 单一数据源。

    按 id 前缀分流到对应 state yaml 目录，返回其 ``title`` 字段：

    - ``req-*`` → ``.workflow/state/requirements/*.yaml``
    - ``bugfix-*`` → ``.workflow/state/bugfixes/*.yaml``
    - ``reg-*`` / 其他前缀：无独立 state yaml，返回空串（由上层 render helper 兜底）
    - 空 id：返回空串

    找不到文件、文件读异常：一律 **返回空串，不抛异常**（null-safe），保证 CLI
    渲染链路永不因 title 查找失败崩溃（AC-04 降级）。
    """
    if not work_item_id:
        return ""
    ident = work_item_id.strip()
    if not ident:
        return ""
    if ident.startswith("req-"):
        state_dir = root / ".workflow" / "state" / "requirements"
    elif ident.startswith("bugfix-"):
        state_dir = root / ".workflow" / "state" / "bugfixes"
    else:
        # reg-* / sug-* / 其他前缀：无独立 state yaml，返回空串
        return ""
    if not state_dir.exists():
        return ""
    try:
        for state_file in sorted(state_dir.glob("*.yaml")):
            try:
                payload = load_simple_yaml(state_file)
            except Exception:  # noqa: BLE001
                continue
            if _get_req_id(payload) == ident:
                return str(payload.get("title", "")).strip()
    except Exception:  # noqa: BLE001
        return ""
    return ""


def _resolve_title_for_suggestion(root: Path, sug_id: str) -> str:
    """req-30 / chg-02：为 sug-NN 查 title，多级 fallback。

    顺序：
    1. `.workflow/flow/suggestions/sug-NN*.md` 的 frontmatter.title
    2. body 首行（前 40 字符截断，去首尾空白）
    3. `.workflow/flow/suggestions/archive/` 下同名文件，重复 1-2
    4. 均无 → 返回空串（由 render helper 兜底为 `(no title)`）
    """
    if not sug_id or not sug_id.startswith("sug-"):
        return ""
    candidate_dirs = [
        root / ".workflow" / "flow" / "suggestions",
        root / ".workflow" / "flow" / "suggestions" / "archive",
    ]
    for base in candidate_dirs:
        if not base.exists():
            continue
        for path in sorted(base.glob("sug-*.md")):
            stem = path.stem
            if stem == sug_id or stem.startswith(sug_id + "-"):
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:  # noqa: BLE001
                    continue
                # 尝试 frontmatter.title
                try:
                    state = load_simple_yaml(path)
                    title = str(state.get("title", "")).strip()
                except Exception:  # noqa: BLE001
                    title = ""
                if title:
                    return title
                # 降级读 body 首行
                parts = text.split("---", 2)
                body = parts[-1] if len(parts) >= 3 else text
                body = body.strip()
                if body:
                    first_line = body.splitlines()[0].strip()
                    if first_line:
                        return first_line[:40]
                return ""
    return ""


def render_work_item_id(
    work_item_id: str,
    *,
    runtime: dict[str, object] | None = None,
    root: Path | None = None,
) -> str:
    """req-30 / chg-02：CLI 渲染层唯一 id→显示字符串转换入口。

    查找顺序（AC-03 / AC-04）：
    1. `runtime` 缓存：按 id 前缀匹配对应 `*_title` 字段（req → `current_requirement_title`
       / `locked_requirement_title`；reg → `current_regression_title`）。
    2. `root` 下 state fallback：`_resolve_title_for_id(root, id)`。
    3. `sug-*` 特殊分支：`_resolve_title_for_suggestion`（读 frontmatter / body 首行）。
    4. 都拿不到 → 返回 ``{id} (no title)`` 降级字符串，永不抛错。

    空 id → 返回 ``"(none)"``（与 `workflow_status` 旧行为兼容）。
    """
    if not work_item_id:
        return "(none)"
    ident = work_item_id.strip()
    if not ident:
        return "(none)"

    title = ""

    # 1. runtime 缓存
    if runtime:
        if ident.startswith("req-") or ident.startswith("bugfix-"):
            # current / locked 均可能命中；优先当前
            current_id = str(runtime.get("current_requirement", "")).strip()
            locked_id = str(runtime.get("locked_requirement", "")).strip()
            if ident == current_id:
                title = str(runtime.get("current_requirement_title", "")).strip()
            elif ident == locked_id:
                title = str(runtime.get("locked_requirement_title", "")).strip()
        elif ident.startswith("reg-"):
            current_reg = str(runtime.get("current_regression", "")).strip()
            if ident == current_reg:
                title = str(runtime.get("current_regression_title", "")).strip()

    # 2. state fallback（req / bugfix）
    if not title and root is not None:
        if ident.startswith("req-") or ident.startswith("bugfix-"):
            title = _resolve_title_for_id(root, ident)
        elif ident.startswith("sug-"):
            # 3. sug 特殊分支
            title = _resolve_title_for_suggestion(root, ident)

    # req-31（批量建议合集（20条））/ chg-05（legacy yaml strip 兜底）/ Step 1（sug-23）：
    # legacy yaml 脏数据 title（前后空格 + 包围 ``'`` / ``"``）render 时 strip 兜底，
    # 保证对人输出干净。``.strip(...)`` 只处理首尾字符，内部合法字符（如 ``foo's bar``
    # 的单引号）不受影响。
    if title:
        title = title.strip().strip("'\"").strip()
    if title:
        return f"{ident}（{title}）"
    return f"{ident} (no title)"


def _render_id_list(
    ids: list[str] | list[object],
    *,
    runtime: dict[str, object] | None = None,
    root: Path | None = None,
) -> str:
    """req-30 / chg-02：批量渲染版本，用于 `active_requirements` 等 list。"""
    if not ids:
        return "(none)"
    return ", ".join(
        render_work_item_id(str(item), runtime=runtime, root=root) for item in ids
    )


def save_requirement_runtime(root: Path, runtime: dict[str, object]) -> None:
    payload = dict(DEFAULT_STATE_RUNTIME)
    payload.update(runtime)
    # req-28 / chg-02（AC-12）：ordered_keys 必须包含 operation_type / operation_target
    # 以及 stage_entered_at，否则 save_simple_yaml 会按白名单裁剪字段，导致
    # `create_bugfix` 写入的 operation_type 在第一次 save→load 往返后丢失，
    # 进而触发 `workflow_next` 走错 sequence → `Unknown stage: regression`。
    # req-30 / chg-01：*_title 字段紧邻对应 id 字段，保持字段顺序稳定可读。
    # req-38 / chg-03：stage_pending_user_action 字段——值为 None 或 {type, details} dict；
    # 旧 runtime.yaml 无该键时 load 返回 None，不抛异常（用 .get 读取）。
    save_simple_yaml(
        root / STATE_RUNTIME_PATH,
        payload,
        ordered_keys=[
            "operation_type",
            "operation_target",
            "current_requirement",
            "current_requirement_title",
            "stage",
            "stage_entered_at",
            "conversation_mode",
            "locked_requirement",
            "locked_requirement_title",
            "locked_stage",
            "current_regression",
            "current_regression_title",
            "ff_mode",
            "ff_stage_history",
            "active_requirements",
            "stage_pending_user_action",
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
                "6. 如果存在 `.claude/skills/harness/SKILL.md`，按主 Harness skill 执行",
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
                "6. If `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill",
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
                "- 如果当前 stage 是 `analysis`，确认 change.md + plan.md 已产出后，再 `harness next` 推进到 executing",
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
                "- if the current stage is `analysis`, confirm change.md + plan.md are produced before running `harness next` to advance to executing",
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
                "path": "analysis/10-request-human-review-first.md",
                "title": {"cn": "分析阶段先等用户确认", "english": "Analysis Stage Waits for Human Confirmation"},
                "body": {
                    "cn": [
                        "如果当前 stage 是 `analysis`，回复应优先请求用户审核 requirement 文档、change 列表与 plan 文档。",
                        "analyst 在 analysis 阶段一次性产出 requirement.md + change.md + plan.md 后，停下等用户确认，不得自动推进到 executing。",
                    ],
                    "english": [
                        "When the current stage is `analysis`, prioritize asking the human to review the requirement document, change list, and plan documents.",
                        "The analyst produces requirement.md + change.md + plan.md in a single analysis pass, then stops for human confirmation before advancing.",
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
                        "只有用户明确确认 plan 无误后，才允许进入 `executing`。",
                    ],
                    "english": [
                        "After a plan is created or updated, this node must stay in plan discussion and review.",
                        "Only after the human explicitly confirms the plan may the workflow move into `executing`.",
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
                "path": "analysis/10-keep-analysis-context-only.md",
                "title": {"cn": "分析阶段只保留分析上下文", "english": "Analysis Stage Keeps Analysis Context Only"},
                "body": {
                    "cn": [
                        "在 `analysis` 阶段，只保留 requirement 文档、范围、验收边界、change 列表、plan 文档、影响范围、风险与必要依赖。",
                        "analyst 一次性产出 requirement.md + change.md + plan.md 后停下等用户确认。",
                        "与后续实现有关的大段代码、旧方案、已不影响分析的讨论细节，可优先 `/compact` 或 `/clear`。",
                    ],
                    "english": [
                        "During `analysis`, keep only the requirement document, scope, acceptance boundaries, change list, plan documents, impact scope, risks, and required dependencies.",
                        "The analyst produces requirement.md + change.md + plan.md in one pass and waits for human confirmation.",
                        "Large implementation details, old solution trails, and discussion details that no longer affect analysis should be compacted or cleared.",
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
                "path": "analysis/10-no-source-code.md",
                "title": {"cn": "分析节点禁止改源码", "english": "No Source Changes in Analysis Stage"},
                "body": {
                    "cn": [
                        "在 `analysis` 阶段，不允许写生产代码或改业务源码。",
                        "允许补 requirement 文档、讨论范围、验收边界、拆分 change 与制定 plan。",
                    ],
                    "english": [
                        "During `analysis`, do not write production code or modify business source files.",
                        "Requirement document updates, scope discussion, acceptance clarification, change splitting, and plan creation are allowed.",
                    ],
                },
            },
            {
                "path": "analysis/20-no-auto-stage-advance.md",
                "title": {"cn": "分析阶段禁止自动推进", "english": "No Automatic Stage Advance During Analysis"},
                "body": {
                    "cn": [
                        "在 `analysis` 阶段，不要自动执行 `harness next`、自动开始编码或自动进入执行阶段。",
                        "如果用户给的是实现细节，也只允许把它吸收进 requirement，随后等待用户确认。",
                    ],
                    "english": [
                        "During `analysis`, do not automatically run `harness next`, start coding, or enter execution.",
                        "If the human provides implementation details, absorb them into the requirement and then wait for confirmation.",
                    ],
                },
            },
            {
                "path": "analysis/10-no-implementation-before-confirmation.md",
                "title": {"cn": "分析阶段确认前禁止开始实现", "english": "No Implementation Before Analysis Confirmation"},
                "body": {
                    "cn": [
                        "在 `analysis` 阶段，不要读取源码做实现准备、不要写生产代码、不要启动实施任务。",
                        "只有用户显式确认 plan 无误后运行 `harness next`，才允许进入 `executing`。",
                    ],
                    "english": [
                        "During `analysis`, do not read source code for implementation prep, write production code, or start execution tasks.",
                        "Only after the human confirms the plan and runs `harness next` may the workflow enter `executing`.",
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


# bugfix-3（新）问题 1：active_agent 持久化到 platforms.yaml，与 enabled[] 解耦。
# install_agent 使用的 agent 词表是 {"claude","codex","cc"}；
# 而 platforms.yaml.enabled[] 用的是 {"cc","codex"}（cc 对应 claude）。
# active_agent 字段统一采用 install_agent 词表（"claude"/"cc"），读取时按需映射。
_AGENT_TO_PLATFORM_KEY = {
    "claude": "cc",
    "cc": "cc",
    "codex": "codex",
}
_AGENT_TO_SKILL_DIR = {
    "claude": ".claude",
    "cc": ".claude",
    "codex": ".codex",
}


def read_active_agent(root: Path) -> str | None:
    """Read platforms.yaml.active_agent; return None if missing (compat mode)."""
    from harness_workflow.backup import read_platforms_config
    config = read_platforms_config(str(root))
    value = config.get("active_agent")
    if isinstance(value, str) and value in _AGENT_TO_PLATFORM_KEY:
        return value
    return None


def write_active_agent(root: Path, agent: str) -> None:
    """Persist active_agent to platforms.yaml, preserving enabled/disabled fields."""
    if agent not in _AGENT_TO_PLATFORM_KEY:
        raise ValueError(f"Unknown agent: {agent!r}")
    from datetime import date as _date  # local import to avoid cycles
    config_path = root / ".workflow" / "state" / "platforms.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, object] = {}
    if config_path.exists():
        try:
            existing = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            existing = {}
    if "enabled" not in existing:
        existing["enabled"] = ["codex", "cc"]
    if "disabled" not in existing:
        existing["disabled"] = []
    existing["active_agent"] = agent
    existing["last_updated"] = str(_date.today())
    config_path.write_text(
        yaml.dump(existing, default_flow_style=False, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _project_skill_targets(root: Path, active_agent: str | None = None) -> list[Path]:
    """Compute skill install targets.

    bugfix-3（新）问题 1：当 active_agent 提供时，只返回该 agent 的 skill 路径；
    否则回退到按 platforms.yaml.enabled[] 的旧行为（兼容旧仓）。
    """
    if active_agent and active_agent in _AGENT_TO_SKILL_DIR:
        return [root / _AGENT_TO_SKILL_DIR[active_agent] / "skills" / "harness"]

    from harness_workflow.backup import read_platforms_config
    config = read_platforms_config(str(root))
    enabled = config.get("enabled", [])

    targets = []
    if "codex" in enabled:
        targets.append(root / ".codex" / "skills" / "harness")
    if "cc" in enabled:
        targets.append(root / ".claude" / "skills" / "harness")
    return targets


def _managed_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_with_hash_guard(path: Path, content: str) -> bool:
    """req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 1（sug-13）：
    写入前读旧内容计算 sha256，写入后核对读回内容 hash 是否等于期望；
    若不匹配（疑似并发覆盖）则回滚并打印 stderr WARNING。

    返回：
      - ``True``：写入并验证通过
      - ``False``：二次校验不匹配，已回滚到旧内容

    设计注记：
      - 本 helper 非真正进程级锁；作为 read-after-write 校验机制，用于检测
        **多生成器刷新同一共享文件** 时的覆盖风险（``update_repo`` 单线程调用）。
      - 调用方负责 ``path.parent`` 的 ``mkdir``（避免反复创建）。
    """
    old_content = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(content, encoding="utf-8")
    written = path.read_text(encoding="utf-8")
    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    written_hash = hashlib.sha256(written.encode("utf-8")).hexdigest()
    if written_hash != expected_hash:
        print(
            f"[update_repo] WARNING: hash mismatch at {path}; rolling back",
            file=sys.stderr,
        )
        path.write_text(old_content, encoding="utf-8")
        return False
    return True


# req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 2（sug-14）：
# "用户自建同路径文件" 判据的模板 hash 白名单。
# 判据策略：``relative → {sha256(历史模板版本内容)}``。
# 为避免维护成本，白名单条目在运行时"按需填充"——当前只保留空集合结构，具体
# hash 由 ``_is_user_authored`` 通过 ``_managed_file_contents`` 反向校验当前生成结果
# 与历史版本一致性（上层 ``_sync_requirement_workflow_managed_files`` 的 ``current ==
# content`` 分支已处理"内容一致"情形；本白名单用于标记"用户自定义的脏数据"）。
#
# 未来扩展：若需要显式保留历史模板 hash（跨版本兼容），在此字典追加条目。
_HARNESS_TEMPLATE_HASHES: dict[str, set[str]] = {
    # "CLAUDE.md": {"<hash_v1>", "<hash_v2>"},
    # 目前按"内容不等 + 未登记"即判为 user-authored；此处为前瞻性预留。
}


# 用户自建判据仅保护 **用户可见 / 可能自定义** 的根级文件；``.workflow/`` 下的
# scaffold 文件属于 harness 内部模板，未登记 hash 的情形一律 adopt（bugfix-3 根因 A
# 已覆盖）。
_USER_AUTHORED_SENSITIVE_FILES: set[str] = {
    "CLAUDE.md",
    "AGENTS.md",
    "SKILL.md",
}


def _is_user_authored(path: Path, relative: str, template_content: str) -> bool:
    """req-31 / chg-03 / Step 2（sug-14）：判断 ``path`` 是否为用户自建文件。

    判定策略：
      1. 仅对 ``_USER_AUTHORED_SENSITIVE_FILES`` 中的根级文件（CLAUDE.md /
         AGENTS.md / SKILL.md 等用户可见文件）启用保护；其它 ``.workflow/`` 下的
         scaffold 文件一律走 adopt 路径（保留 bugfix-3 根因 A 的行为）。
      2. 若 ``_HARNESS_TEMPLATE_HASHES[relative]`` 非空且当前文件 hash 在白名单中
         → 视为 harness 历史模板原件 → 返回 False（可被覆盖）。
      3. 否则：若当前文件 hash 等于即将写入的 template_content hash
         → 视为内容一致的巧合命中（正常 adopt）→ 返回 False。
      4. 其它：视为用户自定义内容 → 返回 True。

    仅在 ``path`` 存在时被调用；不存在时由上层走 ``created`` 分支。
    """
    # 仅对 "用户可见的根级文件" 启用保护；``.workflow/`` 下的 scaffold 一律 adopt
    if relative not in _USER_AUTHORED_SENSITIVE_FILES:
        return False
    try:
        current = path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return False
    current_hash = _managed_hash(current)
    whitelist = _HARNESS_TEMPLATE_HASHES.get(relative, set())
    if current_hash in whitelist:
        return False
    if current_hash == _managed_hash(template_content):
        return False
    return True


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


def _managed_file_contents(
    root: Path,
    language: str,
    include_agents: bool,
    include_claude: bool,
    active_agent: str | None = None,
) -> dict[str, str]:
    """Build the managed-file map.

    bugfix-3（新）问题 1：当 active_agent 被指定时，仅为该 agent 写入
    `.{agent}/commands/*` + `.{agent}/skills/*`，其它 agent 的 commands/skills 不再下发。
    `active_agent is None` 时保持旧的全量行为（兼容旧仓 + force_all_platforms escape hatch）。
    """
    repo_name = root.name
    managed = _scaffold_v2_file_contents(
        root,
        include_agents=include_agents,
        include_claude=include_claude,
        language=language,
    )
    for command in COMMAND_DEFINITIONS:
        markdown = render_agent_command(command["name"], command["cli"], command["hint"], language)
        codex_skill = render_codex_command_skill(command["name"], command["cli"], language)

        if active_agent is None:
            # 兼容模式：全 agent 全量写入（等同旧行为）
            managed[f".claude/commands/{command['name']}.md"] = markdown
            managed[f".codex/skills/{command['name']}/SKILL.md"] = codex_skill
        elif active_agent in ("claude", "cc"):
            managed[f".claude/commands/{command['name']}.md"] = markdown
        elif active_agent == "codex":
            managed[f".codex/skills/{command['name']}/SKILL.md"] = codex_skill
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


def install_local_skills(
    root: Path,
    force: bool = False,
    active_agent: str | None = None,
) -> list[Path]:
    """Install the harness skill tree to selected agent target(s).

    bugfix-3（新）问题 1：`active_agent` 指定时仅向该 agent 的 `.{agent}/skills/harness` 写入；
    未指定时回退 `_project_skill_targets(root)` 旧行为（兼容 `--all-platforms` escape hatch）。
    """
    installed: list[Path] = []
    for target in _project_skill_targets(root, active_agent=active_agent):
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
    """Append a single feedback event to .workflow/state/feedback/feedback.jsonl. Never raises."""
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


def record_subagent_usage(
    root: Path,
    role: str,
    model: str,
    usage: dict[str, object],
    *,
    req_id: str = "",
    stage: str | None = None,
    chg_id: str | None = None,
    reg_id: str | None = None,
    task_type: str = "req",
) -> None:
    """Append one subagent usage entry to .workflow/state/sessions/{req_id}/usage-log.yaml.

    chg-08（stage 耗时 + token 消耗统计 + usage-reporter 对人报告）/
    Scope-A 采集契约：主 agent 每次 Agent 工具返回后，从返回值提取 usage 对象，
    调本 helper 追加到独立机器型文件；同步写 record_feedback_event("subagent_usage", ...)。

    req-43（交付总结完善）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））：
    新增 task_type 参数（OQ-5 default-pick），区分三类任务（req / bugfix / sug）；
    req_id 字段语义扩展为「任务级 id」（可为 req-XX / bugfix-XX / sug-XX）；
    目录路径仍按 .workflow/state/sessions/{任务 id}/usage-log.yaml（兼容既有归档逻辑）。

    格式（YAML list item, append 模式）：
      - ts: <ISO8601>
        task_type: <req|bugfix|sug>
        stage: <stage>
        chg_id: <chg-NN>        # optional
        reg_id: <reg-NN>        # optional
        role: <role>
        model: <model>
        usage:
          input_tokens: N
          output_tokens: N
          cache_read_input_tokens: N
          cache_creation_input_tokens: N
          total_tokens: N
          tool_uses: N
          duration_ms: N

    Never raises.
    """
    try:
        if not req_id:
            return
        sessions_dir = root / ".workflow" / "state" / "sessions" / req_id
        sessions_dir.mkdir(parents=True, exist_ok=True)
        log_path = sessions_dir / "usage-log.yaml"
        ts = datetime.now(timezone.utc).isoformat()
        entry_lines = [
            f"- ts: {ts}",
            f"  task_type: {task_type}",
        ]
        if stage is not None:
            entry_lines.append(f"  stage: {stage}")
        if chg_id:
            entry_lines.append(f"  chg_id: {chg_id}")
        if reg_id:
            entry_lines.append(f"  reg_id: {reg_id}")
        entry_lines.append(f"  role: {role}")
        entry_lines.append(f"  model: {model}")
        entry_lines.append("  usage:")
        for key in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                    "cache_creation_input_tokens", "total_tokens", "tool_uses", "duration_ms"):
            val = (usage or {}).get(key, 0)
            entry_lines.append(f"    {key}: {val}")
        entry_lines.append("")
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write("\n".join(entry_lines) + "\n")
        # Sync to feedback.jsonl for dashboard / reporter consumption
        record_feedback_event(root, "subagent_usage", {
            "ts": ts,
            "task_type": task_type,
            "req_id": req_id,
            "stage": stage,
            "chg_id": chg_id,
            "reg_id": reg_id,
            "role": role,
            "model": model,
            "usage": usage,
        })
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# done 阶段效率聚合 helper（chg-05 / req-41 Scope-效率字段）
# ---------------------------------------------------------------------------

_NO_DATA = "⚠️ 无数据"


def done_efficiency_aggregate(
    root: Path,
    req_id: str,
    slug: str = "",
    *,
    task_type: str = "req",
) -> dict[str, object]:
    """Aggregate efficiency & cost data for the done 交付总结 §效率与成本 section.

    Reads:
    - ``.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml``
      (subagent_usage entries written by record_subagent_usage)
    - req yaml ``stage_timestamps`` (dict {stage: ISO8601} or list of {stage, entered_at})

    req-43（交付总结完善）/ chg-03（per-stage 合并到 stage × role × model 单表渲染）：
    新增 ``stage_role_rows`` 字段（list[dict]），按 (stage, role, model) 三键 group by；
    保留 ``role_tokens`` / ``stage_durations`` 字段（legacy 向后兼容标记）。

    req-43（交付总结完善）/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））：
    新增 ``task_type`` 参数，支持 "req" | "bugfix" | "sug" 三类任务路径切换：
    - "req" → ``.workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml``（默认）
    - "bugfix" / "sug" → ``.workflow/state/sessions/{id}/usage-log.yaml``

    Returns a dict::

        {
            "total_duration_s": int | str,          # seconds or _NO_DATA
            "total_duration_human": str,            # "约 N 分钟" or _NO_DATA
            "total_tokens": dict | str,             # {input, output, cache_read, cache_creation, total} or _NO_DATA
            "stage_durations": list[dict] | str,    # [{stage, entered_at, duration_s}] or _NO_DATA  # legacy
            "role_tokens": list[dict] | str,        # [{role, model, total_tokens, tool_uses}] or _NO_DATA  # legacy
            "stage_role_rows": list[dict] | str,    # [{stage, role, model, input_tokens, ...}] or _NO_DATA (chg-03)
        }

    If any data source is missing or empty, the corresponding field is _NO_DATA.
    禁止编造。
    """
    # Locate usage-log based on task_type (chg-04)
    slug_part = f"-{slug}" if slug else ""
    if task_type == "req":
        req_dir = root / ".workflow" / "flow" / "requirements" / f"{req_id}{slug_part}"
    else:
        # bugfix / sug: usage-log in state/sessions/{id}/
        req_dir = root / ".workflow" / "state" / "sessions" / req_id
    usage_log_path = req_dir / "usage-log.yaml"

    entries: list[dict] = []
    if usage_log_path.exists():
        try:
            import yaml as _yaml  # type: ignore[import]
            raw = _yaml.safe_load(usage_log_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                entries = [e for e in raw if isinstance(e, dict)]
        except Exception:  # noqa: BLE001
            entries = []

    # Aggregate token totals per role × model (legacy role_tokens)
    role_map: dict[tuple[str, str], dict[str, int]] = {}
    for e in entries:
        role = e.get("role", "unknown")
        model = e.get("model", "unknown")
        usage = e.get("usage", {}) if isinstance(e.get("usage"), dict) else {}
        key = (role, model)
        if key not in role_map:
            role_map[key] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "total_tokens": 0,
                "tool_uses": 0,
            }
        for field in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                      "cache_creation_input_tokens", "total_tokens", "tool_uses"):
            role_map[key][field] += int(usage.get(field, 0))

    if not entries:
        return {
            "total_duration_s": _NO_DATA,
            "total_duration_human": _NO_DATA,
            "total_tokens": _NO_DATA,
            "stage_durations": _NO_DATA,
            "role_tokens": _NO_DATA,  # legacy 字段，req-43+ 模板不再渲染
            "stage_role_rows": _NO_DATA,
        }

    # Total token sums across all entries
    total_input = sum(e.get("usage", {}).get("input_tokens", 0) for e in entries if isinstance(e.get("usage"), dict))
    total_output = sum(e.get("usage", {}).get("output_tokens", 0) for e in entries if isinstance(e.get("usage"), dict))
    total_cache_read = sum(e.get("usage", {}).get("cache_read_input_tokens", 0) for e in entries if isinstance(e.get("usage"), dict))
    total_cache_creation = sum(e.get("usage", {}).get("cache_creation_input_tokens", 0) for e in entries if isinstance(e.get("usage"), dict))
    total_all = sum(e.get("usage", {}).get("total_tokens", 0) for e in entries if isinstance(e.get("usage"), dict))

    total_tokens_dict = {
        "input": total_input,
        "output": total_output,
        "cache_read": total_cache_read,
        "cache_creation": total_cache_creation,
        "total": total_all,
    }

    # Role × model rows sorted by total_tokens descending (legacy)
    role_rows = sorted(
        [
            {
                "role": k[0],
                "model": k[1],
                "total_tokens": v["total_tokens"],
                "tool_uses": v["tool_uses"],
            }
            for k, v in role_map.items()
        ],
        key=lambda r: r["total_tokens"],
        reverse=True,
    )

    # chg-03: Stage × role × model group by aggregation
    # key = (stage, role, model)
    stage_role_map: dict[tuple[str, str, str], dict[str, int]] = {}
    for e in entries:
        e_stage = e.get("stage") or "unknown"
        e_role = e.get("role", "unknown")
        e_model = e.get("model", "unknown")
        # Tolerate entries without task_type (pre-chg-01 history entries, default to "req")
        usage = e.get("usage", {}) if isinstance(e.get("usage"), dict) else {}
        key3 = (str(e_stage), str(e_role), str(e_model))
        if key3 not in stage_role_map:
            stage_role_map[key3] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
                "total_tokens": 0,
                "tool_uses": 0,
            }
        for field in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                      "cache_creation_input_tokens", "total_tokens", "tool_uses"):
            stage_role_map[key3][field] += int(usage.get(field, 0))

    # Define stage ordering for sort
    _stage_order_list = [
        "analysis",
        "executing", "testing", "acceptance", "regression", "done",
        # legacy aliases (req-id < 50, history archive read-only)
        "requirement_review", "planning", "ready_for_execution",
    ]

    def _stage_sort_key(row: dict) -> tuple:
        s = row["stage"]
        idx = _stage_order_list.index(s) if s in _stage_order_list else 999
        return (idx, -row["total_tokens"])

    stage_role_rows = sorted(
        [
            {
                "stage": k3[0],
                "role": k3[1],
                "model": k3[2],
                "input_tokens": v3["input_tokens"],
                "output_tokens": v3["output_tokens"],
                "cache_read_input_tokens": v3["cache_read_input_tokens"],
                "cache_creation_input_tokens": v3["cache_creation_input_tokens"],
                "total_tokens": v3["total_tokens"],
                "tool_uses": v3["tool_uses"],
            }
            for k3, v3 in stage_role_map.items()
        ],
        key=_stage_sort_key,
    )

    # Stage duration from req yaml stage_timestamps
    req_yaml_candidates = list(req_dir.glob("*.yaml")) + list(req_dir.glob("*.yml"))
    stage_timestamps: dict[str, str] = {}
    for candidate in req_yaml_candidates:
        if candidate.name == "usage-log.yaml":
            continue
        try:
            import yaml as _yaml2  # type: ignore[import]
            data = _yaml2.safe_load(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "stage_timestamps" in data:
                raw_ts = data["stage_timestamps"]
                if isinstance(raw_ts, dict):
                    stage_timestamps = raw_ts
                elif isinstance(raw_ts, list):
                    for item in raw_ts:
                        if isinstance(item, dict) and "stage" in item and "entered_at" in item:
                            stage_timestamps[item["stage"]] = item["entered_at"]
                break
        except Exception:  # noqa: BLE001
            continue

    stage_order = [
        "analysis", "executing", "testing", "acceptance", "done",
        # legacy aliases (req-id < 50, history archive read-only)
        "requirement_review", "planning",
    ]

    stage_rows: list[dict] = _NO_DATA  # type: ignore[assignment]
    total_duration_s: object = _NO_DATA
    total_duration_human: object = _NO_DATA

    if stage_timestamps:
        from datetime import datetime as _dt, timezone as _tz

        def _parse(ts: str) -> "_dt | None":
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                try:
                    return _dt.fromisoformat(ts)
                except ValueError:
                    continue
            return None

        # Only use pure stage keys (not *_exited_at keys) for ordering
        pure_stage_ts = {k: v for k, v in stage_timestamps.items() if not k.endswith("_exited_at")}
        # Sort stages chronologically by their actual timestamp values (avoids legacy vs new ordering bugs)
        def _ts_sort_key(stage_name: str) -> object:
            parsed = _parse(str(pure_stage_ts[stage_name]))
            if parsed is None:
                # Fall back to stage_order position for unparseable timestamps
                try:
                    return (1, stage_order.index(stage_name))
                except ValueError:
                    return (1, 999)
            return (0, parsed)
        all_stages = sorted(pure_stage_ts.keys(), key=_ts_sort_key)

        rows: list[dict] = []
        for i, stage_name in enumerate(all_stages):
            entered_at = pure_stage_ts[stage_name]
            duration_s: object = _NO_DATA
            if i + 1 < len(all_stages):
                t_start = _parse(str(entered_at))
                t_end = _parse(str(pure_stage_ts[all_stages[i + 1]]))
                if t_start and t_end:
                    duration_s = int((t_end - t_start).total_seconds())
            rows.append({"stage": stage_name, "entered_at": entered_at, "duration_s": duration_s})

        stage_rows = rows

        # Total duration = from first stage to last stage
        if len(all_stages) >= 2:
            t_first = _parse(str(pure_stage_ts[all_stages[0]]))
            t_last = _parse(str(pure_stage_ts[all_stages[-1]]))
            if t_first and t_last:
                secs = int((t_last - t_first).total_seconds())
                total_duration_s = secs
                mins = secs // 60
                if mins >= 60:
                    total_duration_human = f"约 {mins // 60} 小时 {mins % 60} 分钟"
                else:
                    total_duration_human = f"约 {mins} 分钟"

    return {
        "total_duration_s": total_duration_s,
        "total_duration_human": total_duration_human,
        "total_tokens": total_tokens_dict,
        "stage_durations": stage_rows,  # legacy 字段，req-43+ 模板不再渲染
        "role_tokens": role_rows,       # legacy 字段，req-43+ 模板不再渲染
        "stage_role_rows": stage_role_rows,
    }


def set_regression_mode(runtime: dict[str, object], regression_id: str = "") -> dict[str, object]:
    payload = dict(runtime)
    payload["mode"] = "regression" if regression_id else "normal"
    payload["current_regression"] = regression_id
    # req-30 / chg-01：id 清空时 title 同步清空（*_title 由写入侧在落盘前的 save 调用点
    # 按需重新 resolve；set_regression_mode 本身无 root，保守清空即可）。
    if not regression_id:
        payload["current_regression_title"] = ""
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
        payload["locked_requirement_title"] = ""
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
        # req-50/chg-01: ff advances directly to executing (no ready_for_execution in new 5-stage sequence)
        payload.update(
            {
                "stage": "executing",
                "status": "executing",
                "current_task": f"Execute approved work for {select_focus_change(payload) or 'the current version'}",
                "next_action": "Implement the approved plan and keep version state updated.",
                "suggested_skill": "executing-plans",
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan.",
                "approval_required": False,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    # req-50 / chg-01（stage 整合 + next 单入口）: new 5-stage sequence
    if stage == "analysis":
        if not focus_change:
            raise SystemExit("No changes exist yet. Create at least one `harness change` before advancing from analysis.")
        from harness_workflow.validate_contract import check_artifact_placement as _check_ap_a  # noqa: PLC0415
        import pathlib as _pathlib_a  # noqa: PLC0415
        _ap_root_a = _pathlib_a.Path(meta.get("_root", ".")) if "_root" in meta else None
        if _ap_root_a is None:
            print("WARN: artifact-placement lint 跳过（root 未传入 meta），请手工运行 `harness validate --contract artifact-placement`")
        else:
            _ap_result_a = _check_ap_a(_ap_root_a)
            if _ap_result_a != 0:
                raise SystemExit(
                    "ABORT: artifact-placement lint FAIL — analysis → executing 流转被阻塞。"
                    " 请先修复 artifacts/ 下机器型文件位置，再重试 `harness next`。"
                )
        payload.update(
            {
                "stage": "executing",
                "status": "executing",
                "current_task": f"Execute approved work for {focus_change or 'the current version'}",
                "next_action": "Implement the approved plan and keep version state updated.",
                "current_artifact_kind": "change" if focus_change else str(payload.get("current_artifact_kind", "")),
                "current_artifact_id": focus_change or str(payload.get("current_artifact_id", "")),
                "suggested_skill": "executing-plans",
                "assistant_prompt": "Use executing-plans or subagent-driven-development to implement the approved plan.",
                "approval_required": False,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    # ---- legacy stage handlers (req-id < 50, history archive read-only) ----
    if stage == "requirement_review":
        # req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-01（机器型工件路径修复 + 防再犯 lint）
        # analyst stage 退出门禁：requirement_review → planning 流转前跑 artifact-placement lint
        from harness_workflow.validate_contract import check_artifact_placement as _check_ap  # noqa: PLC0415
        import pathlib as _pathlib  # noqa: PLC0415
        _ap_root = _pathlib.Path(meta.get("_root", ".")) if "_root" in meta else None
        if _ap_root is None:
            # fallback: 无法确定 root，仅文档化警告，不阻塞（见 change.md §6 风险 1 缓解）
            print("WARN: artifact-placement lint 跳过（root 未传入 meta），请手工运行 `harness validate --contract artifact-placement`")
        else:
            _ap_result = _check_ap(_ap_root)
            if _ap_result != 0:
                raise SystemExit(
                    "ABORT: artifact-placement lint FAIL — requirement_review → planning 流转被阻塞。"
                    " 请先修复 artifacts/ 下机器型文件位置，再重试 `harness next`。"
                )
        payload.update(
            {
                "stage": "planning",
                "status": "review",
                "current_task": f"Plan reviewed requirement {requirement_id or '(current requirement)'}: split into changes and produce change.md + plan.md + 变更简报.md in one pass",
                "next_action": "Create or refine change.md + plan.md + 变更简报.md for every change, then run `harness next`.",
                "suggested_skill": "writing-plans",
                "assistant_prompt": "Use writing-plans (architect role) to decompose the approved requirement into independently deliverable changes and, for each, produce change.md + plan.md + 变更简报.md in a single planning pass. Stop for human review before advancing.",
                "approval_required": True,
                "stage_entered_at": now_iso,
            }
        )
        return payload

    if stage == "planning":
        if not focus_change:
            raise SystemExit("No changes exist yet. Create at least one `harness change` before advancing.")
        # req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-01（机器型工件路径修复 + 防再犯 lint）
        # analyst stage 退出门禁：planning → ready_for_execution 流转前跑 artifact-placement lint
        from harness_workflow.validate_contract import check_artifact_placement as _check_ap2  # noqa: PLC0415
        import pathlib as _pathlib2  # noqa: PLC0415
        _ap_root2 = _pathlib2.Path(meta.get("_root", ".")) if "_root" in meta else None
        if _ap_root2 is None:
            print("WARN: artifact-placement lint 跳过（root 未传入 meta），请手工运行 `harness validate --contract artifact-placement`")
        else:
            _ap_result2 = _check_ap2(_ap_root2)
            if _ap_result2 != 0:
                raise SystemExit(
                    "ABORT: artifact-placement lint FAIL — planning → ready_for_execution 流转被阻塞。"
                    " 请先修复 artifacts/ 下机器型文件位置，再重试 `harness next`。"
                )
        payload.update(
            {
                "stage": "ready_for_execution",
                "status": "review",
                "current_task": "Review complete. Waiting for execution confirmation",
                "next_action": "Run `harness next --execute` to start implementation.",
                "current_artifact_kind": "change",
                "current_artifact_id": focus_change,
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
    active_agent: str | None = None,
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

    managed_contents = _managed_file_contents(
        root,
        language=language,
        include_agents=include_agents,
        include_claude=include_claude,
        active_agent=active_agent,
    )
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    for relative, content in managed_contents.items():
        path = root / relative
        desired_hash = _managed_hash(content)
        if not path.exists():
            actions.append(f"{'missing' if check else 'created'} {relative}")
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                # req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/
                # Step 1（sug-13）：共享 managed 文件统一走 _write_with_hash_guard
                # 检测并发覆盖。
                _write_with_hash_guard(path, content)
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
                _write_with_hash_guard(path, content)
                refreshed_state[relative] = desired_hash
            continue
        # bugfix-3 根因 A：adopt-as-managed 分支。
        # 目标文件存在但 `managed-files.json` 从未登记该文件的 hash（`relative not in managed_state`），
        # 视为"漏登记"（典型成因：老项目在 scaffold_v2 演进前 install，scaffold 新增/改动了该文件，
        # 但目标项目从未 install/update 过新模板，managed-files.json 缺项）。
        # 既然没有历史 hash 记录作为"用户改过"的证据，默认信任 scaffold 模板覆盖并补录 hash；
        # 保护用户自定义文件的语义由下方兜底 `skipped modified` 承担
        # （已登记但 hash 不匹配 = 用户真改过）。
        if relative not in managed_state:
            # req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/
            # Step 2（sug-14）：adopt-as-managed 判据收紧——目标文件存在且 hash 不在
            # harness 默认模板白名单中 → 判为 user-authored，默认跳过 + stderr 提示；
            # 显式 ``force_managed=True``（CLI ``--force-managed``）才强制覆盖。
            if _is_user_authored(path, relative, content) and not force_managed:
                actions.append(f"skipped user-authored {relative}")
                if not check:
                    print(
                        f"[update_repo] skipping user-authored file {relative}; "
                        f"pass --force-managed (--adopt-as-managed) to force.",
                        file=sys.stderr,
                    )
                continue
            actions.append(f"{'would adopt' if check else 'adopted'} {relative}")
            if not check:
                _write_with_hash_guard(path, content)
                refreshed_state[relative] = desired_hash
            continue
        actions.append(f"skipped modified {relative}")
        # req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/
        # testing 收口 / P2-01：managed_state 已登记但 hash 变化 → 文件被用户手改。
        # 仅 stdout `skipped modified` 对 CI/脚本不可见；补 stderr 以与 line ~2968 的
        # user-authored 分支语义对齐（两者均为"保护用户编辑不被覆盖"）。文案区分：
        # 此处为 user-modified（既有登记 + 改动），line ~2968 为 user-authored（新建）。
        if not check:
            if not force_managed:
                # bugfix-8 / chg-03：透传防御 — 明示 force_managed=False 导致跳过
                print(
                    f"[update_repo] skipping user-modified file {relative}; "
                    f"pass --force-managed to overwrite. (force_managed=False)",
                    file=sys.stderr,
                )
            else:
                # force_managed=True 但走到这里说明上游逻辑未能覆盖该分支（防御性日志）
                print(
                    f"[update_repo] WARNING: skipped modified {relative} despite force_managed=True — "
                    f"unexpected branch; please report.",
                    file=sys.stderr,
                )

    if not check:
        save_requirement_runtime(root, load_requirement_runtime(root))
        _save_managed_state(root, _refresh_managed_state(root, managed_contents, refreshed_state))

    return config, actions


def _sync_scaffold_v2_mirror_to_live(
    root: Path,
    *,
    check: bool,
    force_managed: bool,
) -> list[str]:
    """req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））/
    chg-05（install_repo 末尾追加 mirror→live 全量同步）：

    全量遍历 scaffold_v2 mirror dict，对漏写 / 内容不一致的文件做最后一轮同步：
    - 数据源：``_scaffold_v2_file_contents(root, include_agents=False, include_claude=False, language='cn')``
      （`include_agents` / `include_claude` = False，避免与 install_repo 渲染的项目名模板冲突）。
    - 白名单：复用模块级 ``_SCAFFOLD_V2_MIRROR_WHITELIST``（13 条），覆盖运行时态 / 业务态文件。
    - 协作：放在 `_sync_requirement_workflow_managed_files` 之后调用，多数文件已被 managed sync 处理为
      `current == mirror[relative]`，本 helper 直接 no-op；仅对 drift 残留 / 用户手改 / 未登记文件做
      defense-in-depth 处理。

    req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）注：
    本 helper 反向清理 stale_keys 分支（约第 3506-3531 行）已通过 `if not relative.startswith(".workflow/"):
    continue` 天然过滤 artifacts/ 路径；scaffold_v2 mirror 本身不含 `artifacts/project/` 文件
    （chg-01（契约底座-artifacts-project-豁免）已自证），故不会进入 stale_keys 集合；
    `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 "artifacts/project/" + "/project/" 双条目作 defense-in-depth 兜底。
    （req-52 / chg-02：原注释的旧路径已迁移为 artifacts/project/ 主路径，legacy artifacts/{branch}/project/ 由 /project/ substring 兜底）

    写入策略（六分支）：
      1. 命中白名单 → continue（不动）。
      2. live 不存在 → ``_write_with_hash_guard`` 写入 + 登记 hash + actions ``created (mirror) {rel}``。
      3. live 存在且 ``current == expected`` → no-op，仅兜底登记 hash（保险）。
      4. live 存在且 ``managed_state[relative] == current_hash`` → 已被 managed sync 处理（current 等于
         managed 模板渲染态，但与本 helper 用的 mirror 态不完全一致，如 CLAUDE.md / AGENTS.md），continue。
      5. live 存在且 ``relative in managed_state`` 且 hash 不匹配 → 用户改过；非 ``force_managed`` 时
         stderr 提示并跳过 + actions ``skipped user-modified (mirror) {rel}``；``force_managed=True`` 时
         覆盖 + actions ``overwrote user-modified (mirror) {rel}``。
      6. live 存在且 ``relative not in managed_state`` 且 ``current != expected`` → 非 managed 用户修改
         （未登记 hash 的文件被改过）；保守策略同分支 5：默认 stderr 跳过，``force_managed=True`` 才覆盖。

    返回：actions 列表（汇报到 install_repo Update summary 段）；``check=True`` 时不写盘，仅模拟 actions。
    """
    actions: list[str] = []
    mirror = _scaffold_v2_file_contents(
        root, include_agents=False, include_claude=False, language="cn"
    )
    managed_state = _load_managed_state(root)
    refreshed_state = dict(managed_state)
    drift_count = 0
    for relative in sorted(mirror):
        if any(white in relative for white in _SCAFFOLD_V2_MIRROR_WHITELIST):
            continue
        expected = mirror[relative]
        live = root / relative
        desired_hash = _managed_hash(expected)

        # 分支 2：live 不存在
        if not live.exists():
            actions.append(f"{'would create (mirror)' if check else 'created (mirror)'} {relative}")
            drift_count += 1
            if not check:
                live.parent.mkdir(parents=True, exist_ok=True)
                _write_with_hash_guard(live, expected)
                refreshed_state[relative] = desired_hash
            continue

        current = live.read_text(encoding="utf-8")
        current_hash = _managed_hash(current)

        # 分支 3：内容一致 → no-op，兜底登记 hash
        if current == expected:
            refreshed_state[relative] = desired_hash
            continue

        # 分支 4：managed sync 已处理（current 与 managed 模板等价但与 mirror 不同）
        if managed_state.get(relative) == current_hash:
            # 已属 managed 模板态（如 CLAUDE.md/AGENTS.md 在 install 时按 repo_name 渲染），
            # 不应被 mirror 模板态覆盖（mirror dict 不含这些渲染文件，本分支按设计不会命中；
            # 兜底保留以防未来 mirror dict 扩展）。
            continue

        # 分支 5/6：drift 残留（managed sync 未能消除 / 用户修改 / 未登记文件被改过）
        drift_count += 1
        if force_managed:
            label = "would overwrite user-modified (mirror)" if check else "overwrote user-modified (mirror)"
            actions.append(f"{label} {relative}")
            if not check:
                _write_with_hash_guard(live, expected)
                refreshed_state[relative] = desired_hash
            continue
        # 默认保守：跳过 + stderr 提示
        actions.append(f"skipped user-modified (mirror) {relative}")
        if not check:
            if not force_managed:
                # bugfix-8 / chg-03：透传防御 — 明示 force_managed=False 导致跳过
                print(
                    f"[install_repo:mirror-sync] skipping user-modified file {relative}; "
                    f"pass --force-managed to overwrite. (force_managed=False)",
                    file=sys.stderr,
                )
            else:
                # force_managed=True 但走到这里说明上游逻辑未能覆盖该分支（防御性日志）
                print(
                    f"[install_repo:mirror-sync] WARNING: skipped user-modified {relative} "
                    f"despite force_managed=True — unexpected branch; please report.",
                    file=sys.stderr,
                )

    # ---- 反向清理：managed_state 中登记过但 mirror 已无的死条目 (Fix-A) ----
    # 遍历 set(managed_state.keys()) - set(mirror.keys())：这些文件曾被 install 写入（managed_state
    # 有记录），但当前 scaffold_v2 mirror 已不包含它们（文件已从模板中删除）。
    # 重要：mirror 使用 include_agents=False / include_claude=False，因此 agent 目录文件（.claude/、
    # .codex/、.qoder/、.kimi/ 等）不在 mirror 中，但它们是合法的 managed 文件，不应被反向清理。
    # 只对 .workflow/ 路径文件做反向清理（scaffold_v2 mirror 的覆盖范围）。
    # 白名单跳过业务态目录（运行时产物 / 用户经验 / flow/requirements 等）；
    # 白名单外、live 中仍存在的文件 → 移到 LEGACY_CLEANUP_ROOT 备份（不直删）+ 从 managed_state 摘除。
    stale_keys = set(managed_state.keys()) - set(mirror.keys())
    for relative in sorted(stale_keys):
        # 只处理 .workflow/ 路径文件（scaffold_v2 mirror 覆盖范围）；
        # agent 目录文件（.claude/、.codex/ 等）由 managed sync 管理，跳过。
        if not relative.startswith(".workflow/"):
            continue
        if any(w in relative for w in _SCAFFOLD_V2_MIRROR_WHITELIST):
            continue
        live = root / relative
        if live.exists():
            if check:
                actions.append(f"would remove stale (mirror) {relative}")
            else:
                backup_dest = _unique_backup_destination(root, Path(relative))
                backup_dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(live), str(backup_dest))
                actions.append(
                    f"archived stale (mirror) {relative} → "
                    f"{backup_dest.relative_to(root).as_posix()}"
                )
                refreshed_state.pop(relative, None)
        else:
            # 文件已不在 live（可能上次被手动删除），但 managed_state 仍有记录 → 摘除死条目
            if not check:
                refreshed_state.pop(relative, None)

    if not check:
        _save_managed_state(root, refreshed_state)

    if drift_count > 0:
        actions.append(
            f"synced mirror→live: {drift_count} file(s) processed (created / skipped / overwrote)"
        )
    return actions


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


def cleanup_state_bak_files(root: Path, check: bool) -> list[str]:
    """bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）/
    chg-2（state .bak 残留清理 helper）：

    扫描 `.workflow/state/` 下所有 `*.yaml.bak` 文件（由 `_migrate_state_files` 生成）。
    对每个 .bak 文件：
    - 若同名 `.yaml` 存在 → 视为迁移已完成，删除 .bak（用 unlink，不动 git）。
    - 若同名 `.yaml` 不存在 → 保留 .bak 并 stderr 告警（用户手工恢复）。

    返回 actions 列表；`check=True` 时不写盘，仅报告。
    """
    actions: list[str] = []
    state_dir = root / ".workflow" / "state"
    if not state_dir.exists():
        return actions
    for bak_file in sorted(state_dir.rglob("*.yaml.bak")):
        rel = bak_file.relative_to(root).as_posix()
        yaml_file = bak_file.with_suffix("")  # strips .bak → back to .yaml
        if yaml_file.exists():
            actions.append(
                f"{'would remove' if check else 'removed'} stale bak {rel}"
            )
            if not check:
                bak_file.unlink()
        else:
            actions.append(f"kept orphan bak {rel} (no matching .yaml; manual recovery needed)")
            print(
                f"[install_repo:cleanup-bak] WARNING: orphan bak {rel}: "
                "corresponding .yaml not found; keeping for manual recovery.",
                file=sys.stderr,
            )
    return actions


def init_repo(root: Path, write_agents: bool, write_claude: bool, force_managed: bool = False) -> int:
    # bugfix-9 / chg-01（init_repo force_managed 透传修复）：新增 force_managed 参数并向下传递，
    # 修复 install_repo(force_managed=True) 内部调用 init_repo 时透传断链的问题。
    # harness_init.py / install_agent 调用时保持默认 False（初始化场景不需要强制覆盖）。
    _, actions = _sync_requirement_workflow_managed_files(
        root,
        include_agents=write_agents,
        include_claude=write_claude,
        check=False,
        force_managed=force_managed,
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


def _bootstrap_project_skeleton(root: Path, check: bool = False) -> list[str]:
    """install/update 时把 assets/templates/project-skeleton/ 拷到用户仓 artifacts/project/。

    幂等：已存在的文件 skip（用 write_if_missing），不覆盖用户改动。
    check=True：dry-run，返回会写的 actions 列表，不真写。

    bugfix-13（install 时自动创建 artifacts/project 骨架与索引模板）落地。
    """
    actions: list[str] = []
    skeleton_root = PACKAGE_FS_ROOT / "assets" / "templates" / "project-skeleton"
    if not skeleton_root.exists():
        return actions  # 防御：模板缺失 silent skip
    target_root = root / "artifacts" / "project"
    created: list[str] = []
    skipped: list[str] = []
    for src_file in sorted(skeleton_root.rglob("*")):
        if not src_file.is_file():
            continue
        rel = src_file.relative_to(skeleton_root)
        target = target_root / rel
        if target.exists():
            skipped.append(str(rel))
            continue
        if check:
            actions.append(f"would create artifacts/project/{rel.as_posix()}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(src_file.read_bytes())
            created.append(str(rel))
            actions.append(f"created artifacts/project/{rel.as_posix()}")
    if not check:
        print(
            f"[install_repo] project skeleton: created {len(created)} files / skipped {len(skipped)} files",
            file=sys.stderr,
        )
    return actions


def install_repo(
    root: Path,
    force_skill: bool = False,
    check: bool = False,
    force_managed: bool = False,
    force_all_platforms: bool = False,
    agent_override: str | None = None,
) -> int:
    """req-33 / chg-01：`install_repo` 合并 `update_repo` 职责为单一主实现。

    - `check=True` 走 dry-run（等价原 update_repo --check 分支）：预演 managed
      文件刷新、平台选择交互、init_repo 写盘一律跳过，只输出 "Update summary" +
      "No files were changed."。
    - `force_skill=False`（默认）表示直接 install 路径，运行平台选择交互 / init_repo 等
      install 专属步骤；`force_skill=True` 表示 update 委托路径（由 `update_repo` 空壳
      传入），跳过 install 专属交互，直接进入 update 刷新链。
    - `force_managed` / `force_all_platforms` / `agent_override` 转发给 sync /
      `install_local_skills` 的对应字段，保持原 update_repo 的 CLI 语义。
    """
    # Lazy import to avoid circular dependency
    from harness_workflow.cli import prompt_platform_selection

    # bugfix-8 / chg-03：透传防御 — 入口打印 force_managed 状态，让用户直观看到参数透传。
    print(f"[install_repo] force_managed received: {force_managed}", file=sys.stderr)

    actions: list[str] = []

    # ---- 公共前置（install + update 均执行）----
    if _migrate_workflow_dir(root):
        actions.append("migrated .workflow/ → .workflow/")
    _ensure_workflow_dir_gitignore(root)

    # ---- bugfix-13（install 时自动创建 artifacts/project 骨架与索引模板）：拷模板到 artifacts/project/ ----
    _bootstrap_actions = _bootstrap_project_skeleton(root, check=check)
    for _action in _bootstrap_actions:
        print(f"- {_action}")

    # ---- req-52 / chg-04（接入主流程-stderr日志-端到端CLI验证）：项目级合并行为预热 + 日志输出 ----
    # 三个 scope 大类（constraints / experience / tools）各跑一次 _merge_project_level_files，
    # 触发主路径 / branch-path 兼容路径探测 + stderr 日志（OQ-C = A）。
    # check=True（dry-run）模式下也输出日志，方便 e2e pytest 用 --check 观测。
    for _proj_scope in ("constraints", "experience", "tools"):
        # 主路径（chg-01 OQ-A 无 branch 主路径）
        _main_project = root / "artifacts" / "project" / _proj_scope
        # branch-path 兼容路径（chg-01 双轨过渡）
        _branch = _get_git_branch(root) or "main"
        _legacy_project = root / "artifacts" / _branch / "project" / _proj_scope

        _global_dir_map = {
            "constraints": root / ".workflow" / "context" / "constraints",
            "experience": root / ".workflow" / "context" / "experience",
            "tools": root / ".workflow" / "tools",
        }
        _global_dir = _global_dir_map[_proj_scope]

        # 优先主路径，fallback legacy
        if _main_project.exists():
            _merge_project_level_files(_global_dir, _main_project)
            _project_hits = sum(1 for f in _main_project.rglob("*") if f.is_file())
            _log_project_level_load(root, _proj_scope, _project_hits, fallback_used=False)
        elif _legacy_project.exists():
            _merge_project_level_files(_global_dir, _legacy_project)
            _project_hits = sum(1 for f in _legacy_project.rglob("*") if f.is_file())
            _log_project_level_load(root, _proj_scope, _project_hits, fallback_used=True)
        else:
            # 两条路径均不存在：日志记录 0 文件
            _log_project_level_load(root, _proj_scope, hits=0, fallback_used=False)

    # ---- 吸收 update_repo：feedback.jsonl 一次性迁移（原 L3303-L3327）----
    if not check:
        old_feedback = root / LEGACY_FEEDBACK_LOG
        new_feedback = root / FEEDBACK_LOG
        if old_feedback.exists() and not new_feedback.exists():
            new_feedback.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_feedback), str(new_feedback))
            legacy_dir = old_feedback.parent
            if legacy_dir.exists() and not any(legacy_dir.iterdir()):
                legacy_dir.rmdir()
            actions.append("migrated .harness/feedback.jsonl -> .workflow/state/feedback/feedback.jsonl")
            print(
                "[install_repo] NOTE: migrated .harness/feedback.jsonl -> "
                ".workflow/state/feedback/feedback.jsonl",
                file=sys.stderr,
            )
            print(
                "[install_repo] NOTE: run `git status -s .workflow/state/feedback/ .harness/` "
                "and commit the migration.",
                file=sys.stderr,
            )

    # ---- install 专属：legacy docs/ → .workflow/ 迁移 + 平台选择 + init_repo ----
    # force_skill=True 表示从 update_repo 空壳委托调用，跳过 install 专属交互步骤。
    if not force_skill:
        migration_actions = migrate_legacy_docs_to_workflow(root) if not check else []
        if migration_actions:
            print("Migrated legacy docs/ → .workflow/:")
            for action in migration_actions:
                print(f"- {action}")
            print("")

        # Capture platform state before local skills are installed; otherwise the just-copied
        # qoder skill tree makes a brand-new repository look partially configured.
        active_platforms = get_active_platforms(str(root))
        active_list = [p for p, is_active in active_platforms.items() if is_active]

        if not check:
            skill_paths_first = install_local_skills(root, force=False)
            print("Installed local skills:")
            for skill_path in skill_paths_first:
                print(f"- {skill_path}")

            if not active_list:
                selected = ["codex", "cc"]
                print("\nNew installation: enabling all platforms (codex, cc)")
            else:
                # bugfix-7 / chg-05：已有 active_list 时跳过 questionary 交互，直接复用已有平台配置。
                # 仅首次 install（active_list 为空）走交互入口；存量项目不再卡 Enter。
                print(f"\nCurrent active platforms: {', '.join(active_list)} (keeping existing selection)")
                selected = active_list

            result = sync_platforms_state(selected, str(root))
            if result.get("backed_up"):
                print(f"Backed up: {', '.join(result['backed_up'])}")
            if result.get("restored"):
                print(f"Restored from backup: {', '.join(result['restored'])}")
            if result.get("need_generate"):
                print(f"Generated new: {', '.join(result['need_generate'])}")
            if result.get("kept"):
                print(f"Kept: {', '.join(result['kept'])}")

            # init_repo 内 write_if_missing 已做存在跳过（幂等天然）
            # bugfix-9 / chg-01：透传 force_managed，修复 --force-managed 时 init_repo 内部仍用 False 的断链。
            write_agents = "codex" in selected
            write_claude = "cc" in selected
            init_repo(root, write_agents=write_agents, write_claude=write_claude, force_managed=force_managed)

    # ---- 吸收 update_repo：active_agent 解析（原 L3336-L3350）----
    effective_agent: str | None = None
    if force_all_platforms:
        effective_agent = None
    elif agent_override:
        effective_agent = agent_override
    else:
        active = read_active_agent(root)
        if active is None:
            print("[install_repo] active agent not set; refreshing enabled set (compat mode)")
            effective_agent = None
        else:
            effective_agent = active

    # ---- 吸收 update_repo：skill 刷新分支（原 L3352-L3366）----
    if check:
        if effective_agent:
            actions.append(f"would refresh .{_AGENT_TO_SKILL_DIR[effective_agent][1:]}/skills/harness")
        else:
            actions.append("would refresh .codex/skills/harness")
            actions.append("would refresh .claude/skills/harness")
    else:
        installed = install_local_skills(root, force=True, active_agent=effective_agent)
        for target in installed:
            try:
                rel = target.relative_to(root).as_posix()
            except ValueError:
                rel = str(target)
            actions.append(f"refreshed {rel}")

    # ---- bugfix-7 / chg-02：tool_version 失配检测 → 触发 force_managed full re-sync ----
    # 对比 venv tool_version（__version__，当前代码段）vs 目标项目 managed-files.json::tool_version；
    # 版本不一致时强制走 force_managed=True 路径，确保模板全量刷新。
    managed_state_path = root / MANAGED_STATE_PATH
    if not check and managed_state_path.exists():
        try:
            stored_meta = json.loads(managed_state_path.read_text(encoding="utf-8"))
            stored_version = stored_meta.get("tool_version", "")
            if stored_version and stored_version != __version__:
                print(
                    f"[install_repo] detected new tool_version: {stored_version} → {__version__}; "
                    f"triggering full re-sync (force_managed=True)",
                    file=sys.stderr,
                )
                force_managed = True
        except Exception:
            pass

    # ---- 吸收 update_repo：managed 文件同步（原 L3367-L3376）----
    _, sync_actions = _sync_requirement_workflow_managed_files(
        root,
        include_agents=True,
        include_claude=True,
        check=check,
        force_managed=force_managed,
        active_agent=effective_agent,
    )
    actions.extend(sync_actions)
    actions.extend(cleanup_legacy_workflow_artifacts(root, check))

    # ---- 吸收 update_repo：state / experience / profile（原 L3378-L3389）----
    if not check:
        migrate_actions = _migrate_state_files(root)
        actions.extend(migrate_actions)
        # bugfix-4（harness install 升级清理）/ chg-2（state .bak 残留清理）：
        # _migrate_state_files 生成的 .bak 在迁移成功后应当清理，避免永久驻留。
        bak_actions = cleanup_state_bak_files(root, check=False)
        actions.extend(bak_actions)

    _refresh_experience_index(root)

    if not check:
        _write_project_profile_if_changed(root, actions)

    # req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））/
    # chg-05（install_repo 末尾追加 mirror→live 全量同步）：
    # 在 managed sync + project-profile 写盘之后、Update summary 之前，跑 scaffold_v2 mirror→live
    # 全量同步 helper，让存量项目（无 managed-files.json / 缺登记）也能被推到与 mirror 一致。
    mirror_actions = _sync_scaffold_v2_mirror_to_live(
        root, check=check, force_managed=force_managed
    )
    actions.extend(mirror_actions)

    # ---- 合并后的尾部汇总（统一 Update summary 段，兼容原 update_repo 断言）----
    print("Update summary:")
    for action in actions:
        print(f"- {action}")
    if check:
        print("")
        print("No files were changed.")

    # req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））/
    # chg-02 + chg-06：install 末尾自检（chg-06 解锁触发面，存量项目也跑 audit）。
    _install_self_audit(root)

    # bugfix-8 / chg-04：install 末尾接入 user-write-protected-zones 扫描（信息打印；不强制 ABORT）。
    if not check:
        try:
            from harness_workflow.validate_contract import check_user_write_protected_zones
            violations = check_user_write_protected_zones(root)
            if violations == 0:
                print("[install_repo] user-write-protected-zones: PASS (0 violations)", file=sys.stderr)
            # violations > 0 时 check_user_write_protected_zones 已打印详细日志
        except Exception as exc:
            print(f"[install_repo] user-write-protected-zones check error: {exc}", file=sys.stderr)

    return 0


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
        # bugfix-4（harness install 升级清理）/ chg-3（schema 探测扩 folder 形态 + audit 报告）：
        # 扫描 req-XX/ folder 形态（早期 schema，req-id ≤ 38 legacy 路径），仅输出 audit 警告，
        # 不自动删除或迁移（避免数据丢失；用户手工决定归档或迁移）。
        import re as _re
        _req_folder_pattern = _re.compile(r"^(req|bugfix)-\d+")
        for child in sorted(req_state_dir.iterdir()):
            if child.is_dir() and _req_folder_pattern.match(child.name):
                # folder 形态 req：无对应 .yaml，仅 audit 报告
                sibling_yaml = req_state_dir / f"{child.name}.yaml"
                if not sibling_yaml.exists():
                    actions.append(
                        f"⚠️ 检测到旧 schema folder 形态：{child.name}/，"
                        "建议手动迁移到 req-XX.yaml 或对应新 layout"
                    )
                    print(
                        f"[install_repo:schema-audit] ⚠️ 检测到旧 schema folder 形态："
                        f".workflow/state/requirements/{child.name}/，"
                        "建议手动迁移到 req-XX.yaml 或对应新 layout。",
                        file=sys.stderr,
                    )

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


# req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/
# chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）/ Step 1 绿：
# `.workflow/context/project-profile.md` 相对路径常量，helper 与 update_repo
# 共享；与 project_scanner.PROFILE_REL_PATH 保持一致。
_PROJECT_PROFILE_REL: str = ".workflow/context/project-profile.md"

# 从已有 profile 文件中提取 frontmatter `content_hash:` 字段；匹配失败返回空串。
_PROFILE_CONTENT_HASH_RE = re.compile(r"^content_hash:\s*([0-9a-f]{64})\s*$", re.MULTILINE)


def _extract_profile_content_hash(text: str) -> str:
    """req-32 / chg-02 / Step 1：从 profile 文本 frontmatter 解析 content_hash。

    解析失败（文件损坏 / 字段缺失）返回空串，调用方视为 "无旧 hash" → 走漂移分支
    重建（plan.md Step 4 旧 profile 损坏兜底）。
    """
    m = _PROFILE_CONTENT_HASH_RE.search(text)
    return m.group(1) if m else ""


def _write_project_profile_if_changed(root: Path, actions: list[str]) -> None:
    """req-32 / chg-02 / Step 1-2：update_repo 末尾调用，写盘 + 漂移检测三态。

    - **首次**（目标文件不存在）：写盘 + stderr ``project-profile 已生成（初始 hash: <short7>）``
    - **无漂移**（旧 content_hash == 新）：**不重写**文件 + stderr 静默（避免 generated_at
      漂移触发无意义 git diff）。
    - **有漂移**（不同 / 旧文件损坏）：重写 + stderr ``project-profile 已刷新（hash 漂移：<old7>→<new7>）``

    依赖 project_scanner（chg-01 已交付）；本 helper 不新增扫描逻辑，只做
    "扫 → 渲染 → 比对 → 写 + stderr" 的装配。
    """
    # 延迟 import 避免 module load 时的循环依赖（project_scanner 反向依赖 _managed_hash）
    from .project_scanner import (
        build_project_profile,
        render_project_profile,
    )

    target = root / _PROJECT_PROFILE_REL
    profile = build_project_profile(root)
    new_text = render_project_profile(profile)
    new_hash = _extract_profile_content_hash(new_text)

    old_hash = ""
    if target.exists():
        try:
            old_text = target.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            old_text = ""
        old_hash = _extract_profile_content_hash(old_text)

    if not target.exists():
        # 首次生成
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new_text, encoding="utf-8")
        actions.append(f"generated {_PROJECT_PROFILE_REL}")
        print(
            f"[update_repo] project-profile 已生成（初始 hash: {new_hash[:7]}）",
            file=sys.stderr,
        )
        return

    if old_hash and old_hash == new_hash:
        # 无漂移：保留旧文件（含旧 generated_at），静默跳过
        return

    # 有漂移（包括旧文件损坏 / 字段缺失 → old_hash 为空）
    target.write_text(new_text, encoding="utf-8")
    actions.append(f"refreshed {_PROJECT_PROFILE_REL}")
    old_short = old_hash[:7] if old_hash else "unknown"
    print(
        f"[update_repo] project-profile 已刷新（hash 漂移：{old_short}→{new_hash[:7]}）",
        file=sys.stderr,
    )


def update_repo(
    root: Path,
    check: bool = False,
    force_managed: bool = False,
    force_all_platforms: bool = False,
    agent_override: str | None = None,
) -> int:
    """req-33 / chg-01：空壳委托给合并后的 `install_repo`。

    签名与原 update_repo 严格一致以保持 import 兼容；`force_skill=True` 硬编码
    以保持原 update 行为（`install_local_skills(force=True, ...)`）。
    """
    return install_repo(
        root,
        force_skill=True,
        check=check,
        force_managed=force_managed,
        force_all_platforms=force_all_platforms,
        agent_override=agent_override,
    )


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
      - ``artifacts/{branch}/archive/requirements``（归档，primary 形态）
      - ``.workflow/flow/archive/{branch}/``（归档，branch-aware glob 形态，req-52 / chg-02 改）

    req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 4（sug-19）：
    扩展扫描归档树，避免新建 req id 与已归档 id 冲突。
    """
    max_num = 0
    branch = _get_git_branch(root) or "main"
    # req-52 / chg-02：硬编码 main 改 glob，覆盖任意历史 branch 归档子目录。
    scan_dirs = [
        root / ".workflow" / "state" / "requirements",
        root / ".workflow" / "flow" / "requirements",
        resolve_requirement_root(root),
        root / "artifacts" / branch / "archive" / "requirements",
    ]
    flow_archive = root / ".workflow" / "flow" / "archive"
    if flow_archive.exists():
        for branch_dir in flow_archive.iterdir():
            if branch_dir.is_dir():
                scan_dirs.append(branch_dir)
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
    """Return the next available bugfix-N id.

    req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 4（sug-19）：
    扩展扫描归档树，避免新建 bugfix id 与已归档 id 冲突。
    """
    max_num = 0
    # req-52 / chg-02：硬编码 main 改 glob。
    branch = _get_git_branch(root) or "main"
    static_dirs = [
        root / "artifacts" / "bugfixes",
        root / "artifacts" / branch / "bugfixes",
        root / ".workflow" / "state" / "bugfixes",
        root / ".workflow" / "flow" / "bugfixes",
        root / "artifacts" / branch / "archive" / "bugfixes",
    ]
    flow_archive = root / ".workflow" / "flow" / "archive"
    dynamic_dirs: list[Path] = []
    if flow_archive.exists():
        for branch_dir in flow_archive.iterdir():
            if branch_dir.is_dir():
                dynamic_dirs.append(branch_dir)
    for d in static_dirs + dynamic_dirs:
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



#: req-50（现有流程优化）/ chg-01（5-stage sequence 落地）：
#: req-id >= 50 使用新 5-stage workflow（analysis / executing / testing / acceptance / done）；
#: req-id < 50 保持历史兼容（requirement_review 起始）。
_NEW_WORKFLOW_FROM_REQ_ID = 50


def _use_new_workflow_sequence(req_id: str) -> bool:
    """Return True if req_id should use the new 5-stage workflow sequence (req-50+).

    req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）/
    chg-01（analysis stage 落地 + 5-stage WORKFLOW_SEQUENCE）:
    - req-id >= 50 → True（新 5-stage：analysis / executing / testing / acceptance / done）
    - req-id <= 49 → False（历史兼容：requirement_review 起始的旧流程）
    - 非法 id（空串 / None / 非 req-\\d+ 形式）→ False
    """
    if not req_id:
        return False
    m = re.match(r"^req-(\d+)$", req_id.strip())
    if not m:
        return False
    return int(m.group(1)) >= _NEW_WORKFLOW_FROM_REQ_ID


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
        # chg-01 Step 1.2：create_suggestion 要求 title 必填——从正文首行
        # 截断到 60 字符作为 title（与 apply_suggestion 取 title 的策略一致）。
        first_line = suggestion.splitlines()[0].strip() if suggestion else ""
        fallback_title = first_line[:60].strip() or "done-report suggestion"
        try:
            create_suggestion(root, suggestion, title=fallback_title)
            created.append(suggestion[:40])
        except SystemExit:
            pass

    if created:
        print(f"Created {len(created)} suggestion(s) from done report.")
    return created


_VALID_SUGGEST_PRIORITIES = ("high", "medium", "low")


def create_suggestion(
    root: Path,
    content: str,
    title: str | None = None,
    priority: str = "medium",
) -> int:
    """创建 sug 文件，frontmatter 按契约 6（req-28 / chg-01）的五字段约定落盘。

    req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）Step 1.2：

    - ``title`` 必填（契约 6 要求 `title` 字段齐全，不允许 fallback）；
    - ``priority`` 白名单：``high`` / ``medium`` / ``low``，默认 ``medium``；
    - frontmatter 固定写入五字段：``id`` / ``title`` / ``status`` /
      ``created_at`` / ``priority``；``title`` 用 ``json.dumps(..., ensure_ascii=False)``
      避免引号 / Unicode 噪声。
    """
    ensure_harness_root(root)
    suggestion_content = content.strip()
    if not suggestion_content:
        raise SystemExit("Suggestion content is required.")

    if not title or not str(title).strip():
        raise SystemExit("Suggestion title is required (契约 6).")
    title_text = str(title).strip()

    if priority not in _VALID_SUGGEST_PRIORITIES:
        raise SystemExit(
            f"Invalid suggestion priority: {priority!r} (must be one of {_VALID_SUGGEST_PRIORITIES})."
        )

    suggest_id = _next_suggestion_id(root)
    slug = slugify(title_text or suggestion_content) or "suggestion"
    suggestions_dir = root / ".workflow" / "flow" / "suggestions"
    suggestions_dir.mkdir(parents=True, exist_ok=True)
    suggest_path = suggestions_dir / f"{suggest_id}-{slug}.md"

    created_at = date.today().isoformat()
    title_literal = json.dumps(title_text, ensure_ascii=False)
    frontmatter = (
        "---\n"
        f"id: {suggest_id}\n"
        f"title: {title_literal}\n"
        "status: pending\n"
        f"created_at: {created_at}\n"
        f"priority: {priority}\n"
        "---\n\n"
        f"{suggestion_content}\n"
    )
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
        # req-30 / chg-02（AC-03）：sug-NN 行同时附带 title（frontmatter 或 body 首行），
        # 无 title 时降级为 `{id} (no title)`，不阻断命令。
        rendered_sid = render_work_item_id(sid, runtime=None, root=root)
        print(f"  {rendered_sid} [{status}] ({created}) {summary}")
    return 0


def _append_sug_body_to_req_md(
    root: Path,
    req_id: str,
    dir_name: str,
    sug_id: str,
    sug_title: str,
    sug_body: str,
) -> Path:
    """把 sug body 追加到新 req 的 requirement.md。

    bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）:
    - 所有 req 一律走 flow layout：.workflow/flow/requirements/{dir_name}/requirement.md
    - 在文末追加 ## 合并建议清单 段（多次调用幂等聚合到同一段下）。
    - req_md 不存在时 raise FileNotFoundError（调用方决定是否 abort）。
    - 返回写入的 Path。
    """
    req_md = root / ".workflow" / "flow" / "requirements" / dir_name / "requirement.md"

    if not req_md.exists():
        raise FileNotFoundError(f"requirement.md not found at {req_md}")

    existing = req_md.read_text(encoding="utf-8")
    marker = "## 合并建议清单"
    if marker in existing:
        # 追加到已有段落下（幂等）
        new_text = existing.rstrip("\n") + f"\n\n### {sug_id}（{sug_title}）\n\n{sug_body}\n"
    else:
        new_text = (
            existing.rstrip("\n")
            + f"\n\n{marker}\n\n### {sug_id}（{sug_title}）\n\n{sug_body}\n"
        )

    tmp = req_md.with_suffix(".md.tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(req_md)
    return req_md


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

    # req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） / chg-01（apply / apply-all CLI 路径与内容修复）:
    # AC-02：title 优先取 sug frontmatter `title:` 字段，避免用 content 首行（可能含 `#` 前缀
    # 或格式符，产生路径非法字符 / 语义偏差）。
    sug_title = (state.get("title") or "").strip().strip('"').strip()
    if not sug_title:
        first_line = body.splitlines()[0].strip() if body else ""
        sug_title = first_line[:60].strip() or suggest_id
    title = sug_title

    result = create_requirement(root, title)
    if result == 0:
        # 获取刚创建的 req_id 和 dir_name
        runtime_after = load_requirement_runtime(root)
        new_req_id = str(runtime_after.get("current_requirement", "")).strip()
        slug_part = _path_slug(title)
        new_dir_name = f"{new_req_id}-{slug_part}" if slug_part else new_req_id

        # req-44 / chg-01 AC-02：把 sug.body 真写入新 req requirement.md
        try:
            _append_sug_body_to_req_md(root, new_req_id, new_dir_name, suggest_id, title, body)
        except (FileNotFoundError, OSError):
            # body 写入失败：不阻断 sug archive（与 apply_all 对齐，避免半挂）
            pass

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

    # req-43（交付总结完善）/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）：
    # archive_suggestion 是直接处理路径（不转 req），产出轻量 3 段交付总结
    state_after = load_simple_yaml(archive_path)
    sug_title = str(state_after.get("title", suggest_id)).strip('"').strip()
    sug_slug = slugify(sug_title or suggest_id) or suggest_id
    body_text = archive_path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
    current_branch = _get_git_branch(root) or "main"
    _create_sug_delivery_summary(root, suggest_id, sug_slug, sug_title, "archived", body_text, current_branch)

    print(f"Archived suggestion: {suggest_id} -> {archive_path.relative_to(root)}")
    return 0


def _create_sug_delivery_summary(
    root: Path,
    sug_id: str,
    slug: str,
    title: str,
    action: str,
    body: str,
    current_branch: str = "main",
) -> None:
    """产出 sug 直接处理路径的 3 段轻量交付总结（OQ-1 default-pick B）。

    req-43（交付总结完善）/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）：
    sug 直接处理路径（--apply 不转 req / --archive / --reject）产出轻量 3 段交付总结，
    落 artifacts/{branch}/suggestions/{sug-NN}-{slug}/交付总结.md。
    sug → req 转化路径不重复产出（由对应 req done 阶段兜底）。
    """
    try:
        sug_dir = root / "artifacts" / current_branch / "suggestions" / f"{sug_id}-{slug}"
        sug_dir.mkdir(parents=True, exist_ok=True)
        summary_path = sug_dir / "交付总结.md"
        created_at = date.today().isoformat()
        content = f"""---
sug_id: {sug_id}
title: "{title}"
action: {action}
created_at: {created_at}
---

# sug 交付总结：{sug_id} {title}

## 建议是什么
{body[:300] if body else "（建议内容见 sug 文件）"}

## 处理结果
- 处理方式：{action}
- 处理时间：{created_at}

## 后续
- 若需进一步跟进，请查阅对应 req 或相关文档。
"""
        summary_path.write_text(content, encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass  # best-effort，不阻塞主流程


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

    # req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） / chg-01（apply / apply-all CLI 路径与内容修复）:
    # 1) 路径拼接必须走 `_path_slug` 清洗，与 `create_requirement` 同源；
    #    未清洗的 title 含 `/` / `（）` / 空格 / 引号等时 req_dir 解析 miss → 清单追加静默跳过。
    # 2) 路径：bugfix-11 方向C（废弃三段式分水岭）一律走
    #    .workflow/flow/requirements/{dir_name}/requirement.md
    # 3) 原子顺序：先 tmp.write_text → tmp.replace(req_md) 原子 rename 成功，
    #    才进入 unlink 循环；任一步失败必须打印 stderr 并返回非零、不 unlink。
    if not req_id:
        print("[apply_all] ERROR: current_requirement 为空，无法定位 req_dir，终止前保留所有 body", file=sys.stderr)
        return 1

    slug_part = _path_slug(title)
    dir_name = f"{req_id}-{slug_part}" if slug_part else req_id

    # 逐条 sug body 追加（调用统一 helper，一律走 flow layout）
    for path, suggest_id, suggest_title in pending:
        # 取 sug frontmatter title 优先（与 apply_suggestion 对齐）
        sug_state = load_simple_yaml(path)
        sug_title_fm = (sug_state.get("title") or "").strip().strip('"').strip()
        sug_body = path.read_text(encoding="utf-8").split("---", 2)[-1].strip()
        display_title = sug_title_fm or suggest_title
        try:
            _append_sug_body_to_req_md(root, req_id, dir_name, suggest_id, display_title, sug_body)
        except FileNotFoundError as exc:
            print(
                f"[apply_all] ERROR: req_md missing ({exc}); aborting before unlink",
                file=sys.stderr,
            )
            return 1
        except OSError as exc:
            print(
                f"[apply_all] ERROR: append failed ({exc}); leaving bodies intact",
                file=sys.stderr,
            )
            return 1

    # 清单落盘成功才允许 unlink sug body
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

    # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
    # 所有 req 一律走 flow layout：机器型 requirement.md 落 .workflow/flow/requirements/{req-id}-{slug}/
    # artifacts/ 目录仅放对人文档（§2 白名单内），不建 changes/ 子目录。
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    write_if_missing(
        flow_req_dir / "requirement.md",
        render_template("requirement.md.tmpl", repo_name, config["language"], replacements),
        created,
        skipped,
    )
    # artifacts/ 目录只建根目录，不建 changes/ 子目录（扁平结构约束）
    requirement_dir.mkdir(parents=True, exist_ok=True)

    state_file = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
    if not state_file.exists():
        today = date.today().isoformat()
        # req-50/chg-01: req-id >= 50 使用新 5-stage sequence（analysis 起始）；
        # req-id < 50 保持历史兼容（requirement_review 起始）。
        _initial_stage = "analysis" if _use_new_workflow_sequence(req_num_id) else "requirement_review"
        save_simple_yaml(
            state_file,
            {
                "id": req_num_id,
                "title": requirement_title,
                "stage": _initial_stage,
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
    # req-30 / chg-01：写 id 时同步写 *_title（state yaml 已在前面写入，此处 resolve 必中）。
    runtime["current_requirement_title"] = _resolve_title_for_id(root, req_num_id)
    # req-50/chg-01: req-id >= 50 使用新 5-stage（analysis）；< 50 历史兼容（requirement_review）。
    runtime["stage"] = "analysis" if _use_new_workflow_sequence(req_num_id) else "requirement_review"
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
    created: list[str] = []
    skipped: list[str] = []
    replacements = {"ID": bfx_num_id, "TITLE": bugfix_title}

    # bugfix-11（H-E3 扩范围）：所有 bugfix 无条件走 flow layout，
    # 机器型文档落 .workflow/flow/bugfixes/{dir}/；
    # artifacts/ 路径仅创建 README.md 占位说明"对人产物预留目录"。
    bugfix_dir = root / ".workflow" / "flow" / "bugfixes" / dir_name
    artifacts_dir = root / "artifacts" / branch / "bugfixes" / dir_name
    # 在 artifacts/ 创建占位 README 说明"对人产物预留目录"
    readme_content = (
        f"# {bfx_num_id}（{bugfix_title}）对人产物预留目录\n\n"
        "本目录为对人可读产物（如 SQL 脚本、部署文档、对外报告等）的预留位置。\n"
        "机器型工件（bugfix.md / session-memory.md / regression/diagnosis.md 等）\n"
        f"已迁至 `.workflow/flow/bugfixes/{dir_name}/`。\n\n"
        "如本次 bugfix 有对人产物（如部署脚本），请将其放置于本目录。\n"
    )
    write_if_missing(artifacts_dir / "README.md", readme_content, created, skipped)

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
    # req-30 / chg-01：bugfix id 也走 current_requirement_title 同步（兼容字段语义）。
    runtime["current_requirement_title"] = _resolve_title_for_id(root, bfx_num_id)
    runtime["stage"] = "regression"
    runtime["active_requirements"] = active_reqs
    save_requirement_runtime(root, runtime)

    workspace_dir = bugfix_dir
    print(f"Bugfix workspace: {workspace_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def _next_chg_id(req_dir: Path, root: Path | None = None, req_id: str | None = None) -> str:
    """Return the next available chg-NN id within a requirement.

    bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
    所有 req 一律走 flow layout：扫 .workflow/flow/requirements/{req-id}-{slug}/changes/chg-* 分配 id。
    req_dir 已是 flow req dir；扫其 changes/ 子目录取 max id。
    """
    max_num = 0
    # Flow layout: scan req_dir/changes/chg-* for max id
    changes_dir = req_dir / "changes"
    if changes_dir.exists():
        for item in changes_dir.iterdir():
            if not item.is_dir():
                continue
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
        # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
        # 所有 req 一律走 flow layout：req_dir 在 .workflow/flow/requirements/{req-id}-{slug}/
        req_dir = resolve_requirement_reference(
            root / ".workflow" / "flow" / "requirements", req_ref, config["language"]
        )
    if not req_dir:
        raise SystemExit("No active requirement. Run `harness requirement <title>` first.")

    chg_num_id = change_id.strip() if change_id else _next_chg_id(req_dir, root=root, req_id=req_ref)
    # req-26 / chg-02（合并 B）：`harness change` 生成的目录名必须走统一
    # slugify 清洗，与 regression 命令簇（chg-01）共用 `slugify_preserve_unicode`。
    # 保留 `chg-NN-` 前缀，空格 / 中文冒号等标点一律折叠为 `-`，保持 CJK。
    slug_part = slugify_preserve_unicode(change_title) or "change"
    dir_name = f"{chg_num_id}-{slug_part}"
    created: list[str] = []
    skipped: list[str] = []
    linked_requirement = req_ref
    replacements = {"ID": chg_num_id, "TITLE": change_title, "REQUIREMENT_ID": linked_requirement or "None"}

    # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
    # 所有 req 一律走 flow layout：机器型文档落 .workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/
    flow_chg_dir = req_dir / "changes" / dir_name
    write_if_missing(flow_chg_dir / "change.md", render_template("change.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(flow_chg_dir / "plan.md", render_template("change-plan.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(flow_chg_dir / "regression" / "required-inputs.md", render_template("regression-required-inputs.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(flow_chg_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    change_dir = flow_chg_dir

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
        # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
        # 所有 req 一律走 flow layout：req_dir 在 .workflow/flow/requirements/{req-id}-{slug}/
        req_dir = resolve_requirement_reference(
            root / ".workflow" / "flow" / "requirements", req_ref, config["language"]
        )
    regressions_base = (req_dir / "regressions") if req_dir else (root / ".workflow" / "flow" / "regressions")

    # 分配 reg-NN 前缀（若调用方显式传入 regression_id 且已是 reg-\d+ 形式则沿用，否则按顺序分配）
    if regression_id and re.match(r"^reg-\d+$", regression_id.strip()):
        reg_num_id = regression_id.strip()
    else:
        # bugfix-11 / 方向C：flow layout 扫 regressions_base 分配 id
        max_from_flow = 0
        if regressions_base.exists():
            for item in regressions_base.iterdir():
                if not item.is_dir():
                    continue
                m = re.match(r"reg-(\d+)", item.name)
                if m:
                    max_from_flow = max(max_from_flow, int(m.group(1)))
        reg_num_id = f"reg-{max_from_flow + 1:02d}"

    slug_part = slugify_preserve_unicode(regression_title) or "regression"
    dir_name = f"{reg_num_id}-{slug_part}"
    created: list[str] = []
    skipped: list[str] = []
    # 模板里的 {{ID}} 统一填充为纯 reg-NN（与 runtime.current_regression 一致，
    # 便于后续命令通过 id 反查目录）。
    replacements = {"ID": reg_num_id, "TITLE": regression_title}

    # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
    # 所有 req 一律走 flow layout：机器型文档落
    # .workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/
    regression_dir = regressions_base / dir_name
    write_if_missing(regression_dir / "regression.md", render_template("regression.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "analysis.md", render_template("regression-analysis.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "decision.md", render_template("regression-decision.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "session-memory.md", render_template("session-memory.md.tmpl", repo_name, config["language"], replacements), created, skipped)
    write_if_missing(regression_dir / "meta.yaml", render_template("regression-meta.yaml.tmpl", repo_name, config["language"], replacements), created, skipped)

    runtime["current_regression"] = reg_num_id
    # req-30 / chg-01：reg-* 无独立 state yaml，title 取传入的 regression_title 作为缓存值。
    runtime["current_regression_title"] = regression_title or ""
    save_requirement_runtime(root, runtime)
    record_feedback_event(root, "regression_created", {"regression_id": reg_num_id, "dir_name": dir_name})

    print(f"Regression workspace: {regression_dir}")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")

    # req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03 扩展：
    # regression 创建即是一次"派发诊断师 subagent"动作，主 agent 需要 briefing 作为交接单。
    # 与 workflow_next(execute=True) 的 briefing 链路一致，额外注入 regression_id /
    # regression_title 两字段，方便诊断师直接定位目标。不修改 runtime["stage"]——
    # regression 是并行的确认流，不占用主线 stage。
    req_title_for_brief = str(runtime.get("current_requirement_title", "")).strip()
    if not req_title_for_brief and req_ref:
        req_title_for_brief = _resolve_title_for_id(root, req_ref) or ""
    briefing = _build_subagent_briefing(
        "regression",
        req_ref or "",
        req_title_for_brief,
        root=root,
        regression_id=reg_num_id,
        regression_title=regression_title or "",
    )
    print(briefing)
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
    2. ``.workflow/flow/requirements/{current_requirement}/regressions/``（flow layout）；
    3. ``artifacts/{branch}/regressions/``（无 requirement 时的兜底）；
    4. ``.workflow/flow/regressions/``（legacy 路径）。
    """
    runtime = load_requirement_runtime(root)
    candidates: list[Path] = []
    req_ref = str(runtime.get("current_requirement", "")).strip()
    if req_ref:
        req_dir = resolve_requirement_reference(resolve_requirement_root(root), req_ref, language)
        if req_dir is not None:
            candidates.append(req_dir / "regressions")
        # upstream-fix: also check flow layout (.workflow/flow/requirements/{req}/regressions/)
        flow_req_dir = resolve_requirement_reference(
            root / ".workflow" / "flow" / "requirements", req_ref, language
        )
        if flow_req_dir is not None:
            candidates.append(flow_req_dir / "regressions")
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
        # req-30 / chg-01：id 清空时同步清 *_title 缓存。
        runtime["current_regression_title"] = ""
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
        runtime["current_regression_title"] = ""  # req-30 / chg-01
        save_requirement_runtime(root, runtime)
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return create_change(root, change_title)

    if requirement_title:
        _ensure_regression_experience(root, regression_id)
        runtime["current_regression"] = ""
        runtime["current_regression_title"] = ""  # req-30 / chg-01
        save_requirement_runtime(root, runtime)
        print("Consider summarizing lessons into `context/experience/stage/testing.md` and `context/experience/stage/acceptance.md` if applicable.")
        return create_requirement(root, requirement_title)

    if to_testing:
        _ensure_regression_experience(root, regression_id)
        _update_regression_meta_status(root, regression_id, "testing")
        runtime["current_regression"] = ""
        runtime["current_regression_title"] = ""  # req-30 / chg-01
        runtime["stage"] = "testing"
        save_requirement_runtime(root, runtime)
        # req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 3（sug-16 + sug-21）：
        # regression --testing 子路径显式触发 _sync_stage_to_state_yaml，消除
        # "stage_timestamps.testing 在回退到 testing 时被跳过"的盲区。
        operation_type = str(runtime.get("operation_type", "")).strip()
        operation_target = str(runtime.get("operation_target", "")).strip()
        if not operation_target:
            operation_target = str(runtime.get("current_requirement", "")).strip()
        _sync_stage_to_state_yaml(root, operation_type or "requirement", operation_target, "testing")
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

    # 4) 同步 .workflow/flow/requirements/ 目录（bugfix-6 后新路径，若存在则 mv）。
    # req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） / chg-02（rename CLI 同步范围扩展）AC-03：
    _flow_req_dir = root / ".workflow" / "flow" / "requirements" / old_dir_name
    if _flow_req_dir.is_dir():
        _flow_req_new = root / ".workflow" / "flow" / "requirements" / new_dir_name
        shutil.move(str(_flow_req_dir), str(_flow_req_new))

    # 5) 同步 runtime.yaml：id 不变，但同步 current_requirement_title / locked_requirement_title。
    # req-44 / chg-02 AC-03：rename 时同步 runtime title 字段，使 runtime 与目录名保持一致。
    runtime = load_requirement_runtime(root)
    if str(runtime.get("current_requirement", "")).strip() == old_id:
        runtime["current_requirement_title"] = new_title
    if str(runtime.get("locked_requirement", "")).strip() == old_id:
        runtime["locked_requirement_title"] = new_title
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


# _extract_section 和 generate_requirement_artifact 已由
# req-42（archive 重定义：对人不挪 + 摘要废止）/ chg-02（archive_requirement helper 改写）废止删除。
# archive_requirement 不再生成摘要 md；对人 folder 原位保留（§3.1 archive 行为定义 (ii)）。


def _get_req_id(state: dict[str, object]) -> str:
    """Get requirement id from state, preferring 'id' over legacy 'req_id'."""
    return str(state.get("id", state.get("req_id", ""))).strip()


def _sync_stage_to_state_yaml(
    root: Path,
    operation_type: str,
    operation_target: str,
    new_stage: str,
    *,
    prev_stage: str | None = None,
) -> Path | None:
    """Sync `.workflow/state/{requirements,bugfixes}/{id}.yaml` 的 stage / status。

    req-26 / chg-03（AC-03）双写 helper：
    - 根据 ``operation_type``（requirement/bugfix/suggestion）选择 state 目录；
    - ``operation_target`` 为 id（如 ``req-26`` / ``bugfix-3``），按"直命中 id 字段
      或文件名 stem 前缀匹配 `{id}-`" 两种策略定位 state yaml；
    - 写回 ``stage``；若 ``new_stage == "done"`` 则同步 ``status = "done"`` 与
      ``completed_at``；若文件里存在/可初始化 ``stage_timestamps`` 则打一条时间戳。

    req-43（交付总结完善）/ chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）：
    - 新增可选参数 ``prev_stage``；当 prev_stage 非空且在白名单内时，同级写入
      ``stage_timestamps[{prev_stage}_exited_at]``（D-4 default-pick：同级新键，不嵌套字典，
      向后兼容历史归档 req yaml）。

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

    # req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 2（sug-16 + sug-21）：
    # 对白名单内的 stage，**总是初始化** stage_timestamps 并写入时间戳，消除
    # "state yaml 无 stage_timestamps 字段时 sync 静默跳过"的盲区。白名单限定
    # 避免 apply / suggestion_review 等辅助 stage 引入 schema 漂移。
    now_ts = datetime.now(timezone.utc).isoformat()
    if new_stage in _STAGE_TIMESTAMP_WHITELIST:
        existing = target_state.get("stage_timestamps")
        if not isinstance(existing, dict):
            existing = {}
        # 只在首次写入 entered_at（不覆盖既有值）
        if new_stage not in existing:
            existing[new_stage] = now_ts
        # req-43 / chg-02：同时写 prev_stage 的 exited_at（同级新键，D-4 default-pick）
        if prev_stage and prev_stage in _STAGE_TIMESTAMP_WHITELIST:
            exited_key = f"{prev_stage}_exited_at"
            if exited_key not in existing:
                existing[exited_key] = now_ts
        target_state["stage_timestamps"] = existing

    save_simple_yaml(target_path, target_state)
    return target_path


# req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 2 白名单：
# 仅对主流程 stage 写入时间戳，避免 apply / suggestion_review 等辅助 stage 触发 schema 漂移。
_STAGE_TIMESTAMP_WHITELIST = frozenset({
    "analysis",        # req-50/chg-01: new 5-stage sequence
    "executing",
    "testing",
    "acceptance",
    "regression",
    "done",
    "archive",
    # legacy (req-id < 50, history archive read-only)
    "requirement_review",
    "planning",
    "ready_for_execution",
})

# req-43（交付总结完善）/ chg-02（补齐 stage 流转点时间戳）主流程 stage 顺序
# req-50/chg-01: new 5-stage sequence; legacy stages kept for history archive read-only
_STAGE_ORDER = [
    "analysis", "executing", "testing", "acceptance", "regression", "done",
    # legacy (req-id < 50)
    "requirement_review", "planning", "ready_for_execution",
]


def _backfill_done_timestamps(state: dict[str, object]) -> None:
    """归档前兜底补齐 done.entered_at + 上一 stage._exited_at。

    req-43（交付总结完善）/ chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）：
    若 stage_timestamps 缺少 done 对应的 entered_at，补当前时间；
    同时补上一格（已出现在 stage_timestamps 的最后一个 stage）的 _exited_at。
    向后兼容：对旧 schema（纯 ISO 字符串）和新 schema（含 _exited_at 同级键）均安全。
    """
    now_ts = datetime.now(timezone.utc).isoformat()
    existing = state.get("stage_timestamps")
    if not isinstance(existing, dict):
        return  # 无 stage_timestamps，跳过（兼容无此字段的历史 yaml）

    # 若 done.entered_at 缺失，补当前时间
    if "done" not in existing:
        existing["done"] = now_ts

    # 找到已出现在 stage_timestamps 中、时间戳最晚的非 done、非 *_exited_at stage
    # 按实际时间戳排序（避免 _STAGE_ORDER 中 legacy stages 排序与实际发生顺序不一致的问题）
    prev_stage: str | None = None
    prev_stage_ts: object = None
    for s, ts_val in existing.items():
        if s == "done" or s.endswith("_exited_at"):
            continue
        if prev_stage_ts is None or str(ts_val) > str(prev_stage_ts):
            prev_stage = s
            prev_stage_ts = ts_val

    # 补 prev_stage._exited_at（若缺失）
    if prev_stage:
        exited_key = f"{prev_stage}_exited_at"
        if exited_key not in existing:
            existing[exited_key] = now_ts

    state["stage_timestamps"] = existing


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


def _write_archive_meta(
    archive_dir: Path,
    work_item_id: str,
    title: str,
    origin_stage: str = "done",
) -> None:
    """req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 1（sug-22）：
    归档目录落盘 ``_meta.yaml``，字段含 ``id`` / ``title`` / ``archived_at`` /
    ``origin_stage``。

    幂等保护：若 ``_meta.yaml`` 已存在且含 ``archived_at``，保留原时间戳；仅更新
    ``title`` / ``origin_stage``（避免重复归档刷掉首次归档时间）。

    ``archive_dir`` 必须已存在（由调用方保证）；不存在时静默跳过（兜底，避免崩溃）。
    """
    if not archive_dir.exists():
        return
    meta_path = archive_dir / "_meta.yaml"
    payload: dict[str, object] = {
        "id": work_item_id,
        "title": title or "",
        "archived_at": datetime.now(timezone.utc).isoformat(),
        "origin_stage": origin_stage,
    }
    if meta_path.exists():
        try:
            existing = load_simple_yaml(meta_path)
        except Exception:  # noqa: BLE001
            existing = {}
        if isinstance(existing, dict) and existing.get("archived_at"):
            payload["archived_at"] = existing["archived_at"]
    save_simple_yaml(
        meta_path,
        payload,
        ordered_keys=["id", "title", "archived_at", "origin_stage"],
    )


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

        # 形态 3：req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/
        # Step 2（sug-08）新增——``<branch>/<dir>`` 扁平格式（历史 req-01..26 早期、
        # bugfix 早期归档直接挂在 ``.workflow/flow/archive/<branch>/`` 下，无
        # ``requirements/`` / ``bugfixes/`` 中间层）。按 id 前缀分流到
        # ``artifacts/<branch>/archive/{requirements,bugfixes}/<dir>``。
        # 跳过形态 1 / 2 已覆盖的分流子目录，避免重复枚举。
        for branch_dir in sorted(legacy_root.iterdir()):
            if branch_dir.name in _REQUIREMENT_ROOT_NOISE_FILENAMES:
                continue
            if not branch_dir.is_dir():
                continue
            if branch_dir.name in ("requirements", "bugfixes"):
                continue  # 形态 2
            for child in sorted(branch_dir.iterdir()):
                if child.name in _REQUIREMENT_ROOT_NOISE_FILENAMES:
                    continue
                if not child.is_dir():
                    continue
                if child.name in ("requirements", "bugfixes"):
                    continue  # 形态 1 已枚举
                m = re.match(r"^(req|bugfix)-\d+(?:-|$)", child.name)
                if not m:
                    continue  # 非 id 目录跳过（保留原位）
                kind = "requirements" if m.group(1) == "req" else "bugfixes"
                dst = dst_root / kind / child.name
                pairs.append((child, dst))

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
        # req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 2（sug-08+sug-22）：
        # 扁平归档迁移后落盘 _meta.yaml（origin_stage="legacy-migrated"）。
        m = re.match(r"^(req|bugfix)-(\d+)(?:-(.+))?$", dst.name)
        if m:
            work_item_id = f"{m.group(1)}-{m.group(2)}"
            # title 优先从 state yaml 查；查不到 fallback 到目录名 slug 段
            title = _resolve_title_for_id(root, work_item_id) or (m.group(3) or "")
            _write_archive_meta(dst, work_item_id, title, origin_stage="legacy-migrated")

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



def migrate_bugfix_layout(root: Path, dry_run: bool = False) -> int:
    """把 bugfix-1~5 机器型文档从 artifacts/ 迁移到 .workflow/flow/bugfixes/。

    bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ A5：
    - 源：``artifacts/{branch}/bugfixes/bugfix-{1..5}-{slug}/``（含 .md 机器型文档）
    - 目标：``.workflow/flow/bugfixes/bugfix-{N}-{slug}/``（同结构）
    - 源目录保留，仅添加 README.md 占位说明（default-pick A5-1，不物理删）

    bugfix-6 自身不迁移（在跑流程中，迁了会破坏 session-memory 引用）。

    返回 0 = 成功（含无需迁移），1 = 有冲突。
    """
    import shutil as _shutil

    branch = _get_git_branch(root) or "main"
    artifacts_bugfixes = root / "artifacts" / branch / "bugfixes"
    flow_bugfixes = root / ".workflow" / "flow" / "bugfixes"

    _MACHINE_TYPE_FILES = {
        "bugfix.md",
        "session-memory.md",
        "test-evidence.md",
    }
    _MACHINE_TYPE_IN_REGRESSION = {
        "diagnosis.md",
        "required-inputs.md",
    }

    if not artifacts_bugfixes.exists():
        print("[migrate-bugfix-layout] nothing to migrate (artifacts/bugfixes not found)")
        return 0

    migrated: list[str] = []
    conflicts: list[str] = []
    skipped: list[str] = []

    for bugfix_src in sorted(artifacts_bugfixes.iterdir()):
        if not bugfix_src.is_dir():
            continue
        m = re.match(r"^(bugfix-(\d+))(?:-(.+))?$", bugfix_src.name)
        if not m:
            continue
        bugfix_num = int(m.group(2))
        if bugfix_num >= 6:
            continue  # bugfix-6+ 已走新路径，不迁
        if bugfix_num < 1:
            continue

        bugfix_dst = flow_bugfixes / bugfix_src.name
        label = f"bugfix-{bugfix_num}/{bugfix_src.name}"

        if bugfix_dst.exists():
            skipped.append(label)
            print(f"[migrate-bugfix-layout] skip (already exists): {bugfix_dst.relative_to(root)}")
            continue

        if dry_run:
            print(f"[migrate-bugfix-layout] (dry-run) would migrate {bugfix_src.relative_to(root)} -> {bugfix_dst.relative_to(root)}")
            migrated.append(label)
            continue

        bugfix_dst.mkdir(parents=True, exist_ok=True)

        def _mv(src: Path, dst: Path) -> None:
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                _shutil.move(str(src), str(dst))
                print(f"[migrate-bugfix-layout] {src.relative_to(root)} -> {dst.relative_to(root)}")

        for fname in _MACHINE_TYPE_FILES:
            _mv(bugfix_src / fname, bugfix_dst / fname)

        reg_src = bugfix_src / "regression"
        reg_dst = bugfix_dst / "regression"
        if reg_src.exists():
            for fname in _MACHINE_TYPE_IN_REGRESSION:
                _mv(reg_src / fname, reg_dst / fname)

        readme_path = bugfix_src / "README.md"
        if not readme_path.exists():
            bugfix_id_str = m.group(1)
            title = _resolve_title_for_id(root, bugfix_id_str) or bugfix_src.name
            readme_content = (
                f"# {bugfix_id_str}（{title}）对人产物预留目录\n\n"
                "本目录原有机器型工件（bugfix.md / session-memory.md / regression/diagnosis.md 等）\n"
                f"已由 `harness migrate bugfix-layout` 迁移到 `.workflow/flow/bugfixes/{bugfix_src.name}/`。\n\n"
                "如本 bugfix 有对人产物（如 SQL 脚本、部署文档），请将其放置于本目录。\n"
            )
            readme_path.write_text(readme_content, encoding="utf-8")
            print(f"[migrate-bugfix-layout] created README.md placeholder: {readme_path.relative_to(root)}")

        migrated.append(label)

    if dry_run:
        print(f"[migrate-bugfix-layout] dry-run done: {len(migrated)} would migrate, {len(skipped)} already-at-target")
        return 0

    total = len(migrated) + len(conflicts) + len(skipped)
    if total == 0 and not migrated and not skipped:
        print("[migrate-bugfix-layout] nothing to migrate")
        return 0

    print(f"[migrate-bugfix-layout] done: {len(migrated)} migrated, {len(conflicts)} conflicts, {len(skipped)} already-at-target")
    return 1 if conflicts else 0


def _revert_dry_run_self_check(
    root: Path,
    req_id: str,
    skip_check: bool = False,
) -> int:
    """archive 前置 revert dry-run 自检 helper。

    对本 req 最近 N 个 commit（N = changes/ 目录 chg 数 + 1）执行
    `git revert --no-commit -n <sha>` dry-run 抽样，捕获返回码：

    - 无 conflict → 返回 0；
    - 有 conflict → 输出修复指引 + 返回 1（默认阻塞归档）；
    - skip_check=True → 仅 stderr 警告 + 返回 0（escape hatch）。

    req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
    chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地
    sug-31（done 后 commit + revert dry-run 自动化）。
    """
    import sys

    # 确认 git repo
    git_check = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if git_check.returncode != 0 or git_check.stdout.strip() != "true":
        print("[revert-dry-run] 不在 git 仓库中，跳过检查", file=sys.stderr)
        return 0

    # 计算 changes/ 目录 chg 数
    chg_count = 1  # 默认至少抽样 1 个
    flow_base = root / ".workflow" / "flow" / "requirements"
    if flow_base.exists():
        for req_dir in flow_base.iterdir():
            if req_dir.is_dir() and (req_dir.name.startswith(f"{req_id}-") or req_dir.name == req_id):
                changes_dir = req_dir / "changes"
                if changes_dir.exists():
                    chg_count = max(1, sum(1 for c in changes_dir.iterdir() if c.is_dir()))
                break
    n = chg_count + 1

    # 获取最近 N 个 commit sha
    git_log = subprocess.run(
        ["git", "log", f"--max-count={n}", "--format=%H"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if git_log.returncode != 0:
        print("[revert-dry-run] git log 失败，跳过检查", file=sys.stderr)
        return 0

    commit_shas = [s.strip() for s in git_log.stdout.strip().splitlines() if s.strip()]
    if not commit_shas:
        print("[revert-dry-run] 无 commit 记录，跳过检查", file=sys.stderr)
        return 0

    conflict_shas: list[str] = []

    for sha in commit_shas:
        # 先确保工作区干净（stash 或 reset）—— 仅 dry-run，不产生实际 revert commit
        # dry-run 用法：git revert --no-commit -n <sha>，然后 git revert --abort 或 git checkout -- .
        revert_result = subprocess.run(
            ["git", "revert", "--no-commit", "-n", sha],
            cwd=root,
            capture_output=True,
            text=True,
        )
        # 无论是否冲突，先清理工作区
        subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=root,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "revert", "--abort"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if revert_result.returncode != 0:
            conflict_shas.append(sha)

    if not conflict_shas:
        print(f"[revert-dry-run] PASS：抽样 {len(commit_shas)} 个 commit，revert dry-run 无冲突")
        return 0

    # 有冲突
    print(
        f"[revert-dry-run] {'警告（--skip-revert-check 模式）' if skip_check else 'FAIL'}："
        f"revert 抽样发现冲突（{len(conflict_shas)} / {len(commit_shas)} 个 commit）",
        file=sys.stderr,
    )
    for sha in conflict_shas:
        print(f"  冲突 commit: {sha[:12]}", file=sys.stderr)
    if not skip_check:
        print(
            "提示：revert 抽样发现冲突。可用 'harness archive --skip-revert-check' 强制跳过（保留 escape hatch）",
            file=sys.stderr,
        )
        return 1

    # skip_check=True：仅警告不阻塞
    return 0


def archive_requirement(
    root: Path,
    requirement_name: str,
    folder: str = "",
    force_done: bool = False,
    skip_revert_check: bool = False,
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

    ``skip_revert_check``：为 True 时跳过 revert dry-run 前置自检（保留 escape hatch）。
    req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
    chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地
    sug-31（done 后 commit + revert dry-run 自动化）。
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

    # bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）/ 方向C（废弃三段式分水岭）：
    # 所有 req 一律走 flow layout；is_flow_req 恒为 True（对 req- 前缀），is_bugfix 例外。
    is_flow_req = not is_bugfix and bool(re.match(r"^req-\d+$", raw_ref.strip()))

    if is_bugfix:
        source_root = resolve_bugfix_root(root)
        state_subdir = "bugfixes"
        archive_subdir = "bugfixes"
    elif is_flow_req:
        source_root = root / ".workflow" / "flow" / "requirements"
        state_subdir = "requirements"
        archive_subdir = "requirements"
    else:
        # 兜底：非 req- 前缀、非 bugfix 类型（不应正常触发，保留安全出口）
        source_root = resolve_requirement_root(root)
        state_subdir = "requirements"
        archive_subdir = "requirements"

    req_dir = resolve_requirement_reference(source_root, raw_ref, "cn")
    if not req_dir:
        raise SystemExit(f"{kind_label.capitalize()} does not exist: {requirement_name}")

    # --- revert dry-run 前置自检（sug-31（done 后 commit + revert dry-run 自动化）落地）---
    # 仅对 requirement（非 bugfix）跑 revert dry-run；
    # skip_revert_check=True 时仅警告不阻塞（escape hatch）。
    if not is_bugfix:
        _rc_revert = _revert_dry_run_self_check(root, raw_ref, skip_check=skip_revert_check)
        if _rc_revert != 0:
            return _rc_revert

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

    if is_flow_req:
        # req-41（机器型工件回 flow/requirements）/ chg-02（CLI 路径迁移 flow layout）:
        # flow 路径：target = .workflow/flow/archive/{branch}/req-{req-id}-{slug}/
        flow_archive_base = root / ".workflow" / "flow" / "archive"
        target_parent = flow_archive_base / current_branch
        target_parent.mkdir(parents=True, exist_ok=True)
        target = target_parent / req_dir.name
        shutil.move(str(req_dir), str(target))
    else:
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

    # req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 1+5（sug-22）：
    # 归档目录落盘 _meta.yaml（origin_stage="done"，因为走的是正常归档路径）。
    m_archive = re.match(r"^(req|bugfix)-(\d+)(?:-(.+))?$", target.name)
    if m_archive:
        archive_work_item_id = f"{m_archive.group(1)}-{m_archive.group(2)}"
        archive_title = _resolve_title_for_id(root, archive_work_item_id) or (m_archive.group(3) or "")
        _write_archive_meta(target, archive_work_item_id, archive_title, origin_stage="done")

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
                # req-43（交付总结完善）/ chg-02（补齐 stage 流转点时间戳）：
                # 归档前兜底补齐 done.entered_at + 上一 stage._exited_at（断电式归档遗漏防护）。
                _backfill_done_timestamps(state)
                save_simple_yaml(req_file, state)
                # Migrate state.yaml to archive directory
                shutil.move(str(req_file), str(target / "state.yaml"))
                break

    # bugfix-11 / 方向C：三段式分水岭废弃后，state/requirements/{req-id}/ 子目录
    # 仅存 req-39/40 历史遗留（flat layout）；flow layout req 的机器型文档已在
    # .workflow/flow/requirements/{req-id}-{slug}/ 内，随整个 folder 整体迁移，无需额外处理。
    # 对存量 req-39/40 的归档行为：若 state/requirements/{req-id}/ 目录仍存在，照旧迁移到 state_requirements/。
    if archived_req_id and not is_bugfix and not is_flow_req:
        state_req_machine_dir = root / ".workflow" / "state" / "requirements" / archived_req_id
        if state_req_machine_dir.exists():
            state_machine_dst = target / "state_requirements"
            state_machine_dst.mkdir(parents=True, exist_ok=True)
            for f in state_req_machine_dir.iterdir():
                shutil.move(str(f), str(state_machine_dst / f.name))
            try:
                state_req_machine_dir.rmdir()
            except OSError:
                pass
            print(f"Migrated state/requirements/{archived_req_id}/: {state_machine_dst.relative_to(root)}")

    # Update runtime active_requirements
    active_reqs = [str(r) for r in runtime.get("active_requirements", []) if str(r) != archived_req_id]
    runtime["active_requirements"] = active_reqs
    current_req = str(runtime.get("current_requirement", "")).strip()
    # req-28 / chg-03：归档 bugfix 不应意外切走 current_requirement（如主 req-28）。
    # 仅当 current_requirement 精确等于被归档 id（或目录名中含之）时才清空/重定向。
    if current_req == archived_req_id or (archived_req_id and current_req == raw_ref):
        new_current = active_reqs[0] if active_reqs else ""
        runtime["current_requirement"] = new_current
        # req-30 / chg-01：id 切换时同步刷新 *_title 缓存。
        runtime["current_requirement_title"] = _resolve_title_for_id(root, new_current) if new_current else ""
    # req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 1（sug-27）：
    # 归档成功后 ff_mode 强制关闭；req-31 AC-自证依赖本行确保本 req 完成后
    # runtime.yaml.ff_mode == false。
    _reset_ff_mode_after_done_archive(runtime, "archive")
    save_requirement_runtime(root, runtime)

    # Migrate state/sessions/{id}/ to archive directory（仅 requirement 分支保留 sessions 迁移）
    # flow req 的 sessions 已内嵌于 .workflow/flow/requirements/ 子树，随整目录移动，无需额外迁移。
    if archived_req_id and not is_bugfix and not is_flow_req:
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

    # Generate artifact document：已由 req-42（archive 重定义：对人不挪 + 摘要废止）/
    # chg-02（archive_requirement helper 改写）废止。
    # generate_requirement_artifact 函数体已删除；对人 folder 原位保留，不生成摘要 md。

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
    current_regression = str(runtime.get("current_regression", "")).strip()
    effective_requirement = locked_requirement or current_requirement
    # req-30 / chg-02（AC-03）：CLI stdout 打印 id 时同行附带 title。
    print(f"current_requirement: {render_work_item_id(current_requirement, runtime=runtime, root=root)}")
    print(f"stage: {str(runtime.get('stage', '')).strip() or '(none)'}")
    print(f"conversation_mode: {runtime.get('conversation_mode', 'open')}")
    print(f"locked_requirement: {render_work_item_id(locked_requirement, runtime=runtime, root=root)}")
    print(f"locked_stage: {str(runtime.get('locked_stage', '')).strip() or '(none)'}")
    print(f"current_regression: {render_work_item_id(current_regression, runtime=runtime, root=root)}")
    active_requirements = runtime.get("active_requirements", [])
    if isinstance(active_requirements, list):
        rendered_active = _render_id_list(active_requirements, runtime=runtime, root=root)
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
    # req-38 / chg-03：pending 行——非空时显示 type + key_details；空/缺失时显示 None。
    pending = runtime.get("stage_pending_user_action")
    if isinstance(pending, dict) and pending:
        typ = pending.get("type", "unknown")
        key_details = _render_key_details(pending.get("details", {}))
        detail_str = f"({key_details})" if key_details else ""
        print(f"Pending User Action: {typ}{detail_str}")
    else:
        print("Pending User Action: None")
    return 0


def workflow_status_lint(root: Path) -> int:
    """``harness status --lint`` — 契约 7 扫描入口。

    req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 3
    （覆盖 sug-25 `harness status --lint` 自动化契约 7 校验）。

    扫描范围由 ``validate_contract.collect_lint_paths`` 统一提供，默认排除
    ``artifacts/{branch}/archive/``。发现违规即非零退出，stdout 按
    ``<file>:<line>: contract-7 bare id <id> — <excerpt>`` 打印便于定位。
    """
    from harness_workflow.validate_contract import (
        check_contract_7,
        collect_lint_paths,
    )

    paths = collect_lint_paths(root)
    violations = check_contract_7(root, paths)
    for v in violations:
        try:
            rel = v.file.relative_to(root)
        except ValueError:
            rel = v.file
        print(f"{rel}:{v.line}: contract-7 bare id {v.work_item_id} — {v.excerpt}")
    if violations:
        print(f"[status --lint] contract-7 violations: {len(violations)}")
        return 1
    print("[status --lint] contract-7 check passed (0 violations).")
    return 0


# req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 6（sug-09）
_STAGE_TO_ROLE: dict[str, str] = {
    "analysis": "analyst（分析师）",  # req-50/chg-01: new 5-stage sequence
    "executing": "executing（开发者）",
    "testing": "testing（测试工程师）",
    "acceptance": "acceptance（验收官）",
    "regression": "regression（诊断师）",
    "done": "done（主 agent）",
    # legacy (req-id < 50, history archive read-only)
    "requirement_review": "requirement-review（需求分析师）",
    "planning": "planning（架构师）",
    "ready_for_execution": "executing（开发者）",
}

_NO_BRIEFING_STAGES = frozenset({"done", "archive", "completed", "ready_for_execution"})  # legacy ready_for_execution kept


def _build_subagent_briefing(
    new_stage: str,
    req_id: str,
    req_title: str,
    *,
    root: Path | None = None,
    task_context_index: list[dict] | None = None,
    task_context_index_file: str = "",
    regression_id: str = "",
    regression_title: str = "",
) -> str:
    """构造 subagent briefing 文本（固定 JSON fence）。

    req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 6（sug-09）：
    供主 agent 在 `harness next --execute` 后直接复制使用；格式稳定，便于解析。

    req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO
    派发 briefing 注入 task_context_index + 快照落盘）：在 JSON fence 中追加
    ``task_context_index`` 数组（≤ 8 条，每条 ``{"path", "reason"}``）与
    ``task_context_index_file``（快照相对路径）。两者均为可选，未传时缺省为空
    数组 / 空串，向后兼容既有测试基线。序列化走 ``json.dumps``，保证 JSON 合法。

    req-32 / chg-03 扩展（ff --auto / regression 派发）：新增三个可选 kwarg，
    全部向后兼容：

    - ``root``：若传入且 ``task_context_index`` 未显式传入，helper 内部调用
      ``_build_task_context_index`` + ``_write_task_context_snapshot`` 自动构建
      索引并落盘，便于 ff_auto / regression 派发点直接一行调用。
    - ``regression_id`` / ``regression_title``：非空时在 briefing JSON 中追加
      ``"regression_id"`` / ``"regression_title"`` 两字段，供 regression 诊断
      子 agent 在 briefing 里直接拿到诊断目标 id / 标题。未传时字段不出现，
      既有测试基线（``test_task_context_index`` 等）完全不受影响。
    """
    import json as _json

    role = _STAGE_TO_ROLE.get(new_stage, new_stage)
    req_title_safe = req_title or "(no title)"
    idx_list: list[dict] = list(task_context_index or [])
    idx_file_str: str = task_context_index_file or ""
    # req-32 / chg-03 扩展：若调用方未显式传 index 但传了 root + req_id + 非终局 stage，
    # 则自动构建索引并落盘，减少 ff_auto / regression 派发点的样板代码。
    if (
        not idx_list
        and not idx_file_str
        and root is not None
        and req_id
        and new_stage
        and new_stage not in _NO_BRIEFING_STAGES
    ):
        try:
            idx_list = _build_task_context_index(
                root=root, stage=new_stage, req_id=req_id
            )
            snap = _write_task_context_snapshot(
                root=root, req_id=req_id, stage=new_stage, index=idx_list
            )
            try:
                idx_file_str = str(snap.relative_to(root))
            except ValueError:
                idx_file_str = str(snap)
        except Exception:
            # 索引构建失败不应阻断派发；degrade to empty index。
            idx_list = []
            idx_file_str = ""
    # 用 json.dumps 序列化 index 数组，避免手工拼接带来的转义问题
    idx_json = _json.dumps(idx_list, ensure_ascii=False, indent=4)
    # 把 4 空格缩进再整体 shift 两格，让其与外层 "  \"task_context_index\": " 对齐
    idx_json_indented = "\n".join(("  " + line) if line else line for line in idx_json.splitlines())
    idx_file_json = _json.dumps(idx_file_str, ensure_ascii=False)
    lines = [
        "```subagent-briefing",
        "{",
        f'  "role": "{role}",',
        f'  "stage": "{new_stage}",',
        f'  "requirement_id": "{req_id}",',
        f'  "requirement_title": "{req_title_safe}",',
    ]
    # regression_id / regression_title 仅在非空时写入，保持向后兼容
    if regression_id:
        reg_id_json = _json.dumps(regression_id, ensure_ascii=False)
        reg_title_json = _json.dumps(regression_title or "", ensure_ascii=False)
        lines.append(f'  "regression_id": {reg_id_json},')
        lines.append(f'  "regression_title": {reg_title_json},')
    lines.extend([
        f'  "task_context_index": {idx_json_indented.lstrip()},',
        f'  "task_context_index_file": {idx_file_json},',
        '  "context_chain": [',
        f'    {{"level": 0, "agent": "main", "stage": "{new_stage}"}}',
        "  ]",
        "}",
        "```",
    ])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO
# 派发 briefing 注入 task_context_index + 快照落盘）
# ---------------------------------------------------------------------------
_TASK_CONTEXT_INDEX_MAX: int = 8
"""req-32 / chg-03：task_context_index 硬上限，超限截断 + stderr warn。"""


def _stage_role_name(stage: str) -> str:
    """req-32 / chg-03：从 stage 反推对应的 role 文件名（裸名，不含 .md 后缀）。

    与 ``_STAGE_TO_ROLE`` 的区别：该表里的 value 含中文括注（如 ``executing（开发者）``），
    此处只需要文件名基底（``executing``）。若 stage 无明确映射，直接返回 stage 字符串。
    """
    mapping = {
        "analysis": "analyst",  # req-50/chg-01: new 5-stage sequence
        "executing": "executing",
        "testing": "testing",
        "acceptance": "acceptance",
        "regression": "regression",
        "done": "done",
        # legacy (req-id < 50, history archive read-only)
        "requirement_review": "requirement-review",
        "planning": "planning",
        "ready_for_execution": "executing",
    }
    return mapping.get(stage, stage)


def _build_task_context_index(
    *,
    root: Path,
    stage: str,
    req_id: str,
) -> list[dict]:
    """req-32 / chg-03 / Step 2：构建任务级上下文索引（≤ 8 条）。

    按优先级从高到低排列候选，仅保留实际存在的文件，最后按 ``_TASK_CONTEXT_INDEX_MAX``
    硬上限截断。优先级：

    1. 当前 stage 对应 role 文件（``.workflow/context/roles/{role}.md``）
    2. ``roles/stage-role.md``
    3. ``roles/base-role.md``
    4. stage 经验（``experience/roles/{role}.md`` / ``experience/stage/{stage}.md``）
    5. 项目 profile（``context/project-profile.md``，若存在）
    6. 约束：risk / boundaries / recovery
    7. checklist（review-checklist.md）

    截断时向 stderr 打印 warn 一行，便于 CI / 人工观察。
    """
    role = _stage_role_name(stage)
    review_stages = {"testing", "acceptance", "done"}

    candidates: list[tuple[str, str]] = []

    def _add(rel: str, reason: str) -> None:
        if not rel:
            return
        # 去重
        if any(path == rel for path, _ in candidates):
            return
        candidates.append((rel, reason))

    # 1-3：默认角色集
    _add(f".workflow/context/roles/{role}.md", "当前 stage 角色文件")
    _add(".workflow/context/roles/stage-role.md", "stage 公共规约（继承链父类）")
    _add(".workflow/context/roles/base-role.md", "agent 通用规约（继承链根）")

    # 4：经验
    _add(f".workflow/context/experience/roles/{role}.md", f"{role} 角色经验沉淀")
    _add(f".workflow/context/experience/stage/{stage}.md", f"{stage} stage 经验沉淀")

    # 5：project profile（若存在）
    profile_rel = ".workflow/context/project-profile.md"
    if (root / profile_rel).exists():
        _add(profile_rel, "项目结构化描述（req-32 动态上下文生成落地）")

    # 6：约束
    _add(".workflow/constraints/risk.md", "风险扫描规则（before-task 必读）")
    _add(".workflow/constraints/boundaries.md", "行为边界细则")
    _add(".workflow/constraints/recovery.md", "失败恢复路径")

    # 7：checklist（仅 review 类 stage）
    if stage in review_stages:
        _add(".workflow/context/checklists/review-checklist.md", "review 阶段检查清单")

    # 仅保留实际存在的文件，保持原序
    existing: list[tuple[str, str]] = [(p, r) for p, r in candidates if (root / p).exists()]

    truncated = False
    original_count = len(existing)
    if original_count > _TASK_CONTEXT_INDEX_MAX:
        existing = existing[:_TASK_CONTEXT_INDEX_MAX]
        truncated = True

    if truncated:
        print(
            f"[briefing] task_context_index truncated from {original_count} to {_TASK_CONTEXT_INDEX_MAX} "
            f"(req_id={req_id}, stage={stage})",
            file=sys.stderr,
        )

    return [{"path": p, "reason": r} for p, r in existing]


def _next_task_context_seq(root: Path, req_id: str, stage: str) -> int:
    """req-32 / chg-03 / Step 3：扫描快照目录计算下一个 seq（从 1 起）。"""
    base = root / ".workflow" / "state" / "sessions" / req_id / "task-context"
    if not base.exists():
        return 1
    pattern = re.compile(rf"^{re.escape(stage)}-(\d+)\.md$")
    max_seq = 0
    for p in base.iterdir():
        if not p.is_file():
            continue
        m = pattern.match(p.name)
        if m:
            try:
                n = int(m.group(1))
                if n > max_seq:
                    max_seq = n
            except ValueError:
                continue
    return max_seq + 1


def _write_task_context_snapshot(
    *,
    root: Path,
    req_id: str,
    stage: str,
    index: list[dict],
) -> Path:
    """req-32 / chg-03 / Step 3：落盘任务级上下文快照。

    路径：``.workflow/state/sessions/{req_id}/task-context/{stage}-{seq:03d}.md``
    frontmatter：``req_id`` / ``stage`` / ``ts`` / ``index_count`` 四字段。
    正文：每行 ``{path}: {reason}``，与 briefing 内索引等价。

    归档由既有 ``harness archive`` 逻辑处理整个 ``sessions/{req_id}/`` 目录，
    本 helper 不重复实现归档。
    """
    if not req_id:
        raise ValueError("_write_task_context_snapshot requires req_id")
    if not stage:
        raise ValueError("_write_task_context_snapshot requires stage")

    seq = _next_task_context_seq(root, req_id, stage)
    base = root / ".workflow" / "state" / "sessions" / req_id / "task-context"
    base.mkdir(parents=True, exist_ok=True)
    target = base / f"{stage}-{seq:03d}.md"

    ts = datetime.now(timezone.utc).isoformat()
    lines: list[str] = [
        "---",
        f"req_id: {req_id}",
        f"stage: {stage}",
        f"ts: {ts}",
        f"index_count: {len(index)}",
        "---",
        "",
    ]
    for item in index:
        path = str(item.get("path", "")).strip()
        reason = str(item.get("reason", "")).strip()
        lines.append(f"{path}: {reason}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _resolve_task_context_paths(
    index: list[dict],
    root: Path,
) -> tuple[list[str], list[str]]:
    """req-32 / chg-03 / Step 5 / AC-04：把 index 分流为 (existing, missing)。

    C2 回退语义：subagent 拿到 briefing 后按此 helper 过滤不存在的条目，对
    ``missing`` 中的路径应静默降级到 ``.workflow/context/index.md`` 全量加载。
    CLI 层不强制约束 subagent 行为（subagent 是 LLM 消费者），仅在此提供
    helper 与单测覆盖。
    """
    existing: list[str] = []
    missing: list[str] = []
    for item in index or []:
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        if (root / path).exists():
            existing.append(path)
        else:
            missing.append(path)
    return existing, missing


# req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 1（sug-27）
_FF_RESET_TERMINAL_STAGES = frozenset({"done", "archive", "completed"})


def _reset_ff_mode_after_done_archive(runtime: dict, new_stage: str) -> dict:
    """当 stage 翻到终局（done / archive / completed）时强制关 ``ff_mode``。

    req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 1（sug-27
    `ff_mode` 在 done / archive 后应自动关闭）。统一入口，替代历史上散落在
    `workflow_next` / `archive_requirement` / `workflow_ff_auto` 的手工重置逻辑；
    req-31 AC-自证依赖本 helper 确保本 req 完成后 runtime.yaml.ff_mode == false。

    入参 ``runtime`` 为 dict 的引用，返回同一个引用（in-place 修改）以便链式调用。
    """
    if (new_stage or "").strip() in _FF_RESET_TERMINAL_STAGES and runtime.get("ff_mode"):
        runtime["ff_mode"] = False
    return runtime


# bugfix-3 / 缺陷 1（sug-12 复发）：合法路由 stage 白名单（含三套 sequence + legacy stages 的并集）。
# upstream-fix: legacy stages（requirement_review / planning / ready_for_execution）也须被允许作为路由目标，
# 否则 req-id < 50 的回退路由（regression decision route_to: planning 等）被误丢弃。
_REGRESSION_ROUTE_VALID_STAGES = frozenset(
    set(WORKFLOW_SEQUENCE) | set(BUGFIX_SEQUENCE) | set(SUGGESTION_SEQUENCE)
    | {"requirement_review", "planning", "ready_for_execution"}
)


def _parse_decision_route(text: str) -> str | None:
    """从 regression decision.md 文本中解析路由 stage。

    bugfix-3 / 缺陷 1（sug-12 复发，``harness next`` 在 regression 后吞 stage）：
    诊断师在 ``decision.md`` 写"路由：planning"等指示，``harness next`` 必须可机读
    优先级：

    1. yaml frontmatter ``route_to: <stage>``（推荐写法，模板已加占位）
    2. 文本 marker：``路由[:：=]\\s*(\\w+)`` / ``harness next\\s*[→\\->\\s]+(\\w+)`` /
       英文 ``route\\s*[:：=]\\s*(\\w+)``
    3. 返回值必须落在 ``_REGRESSION_ROUTE_VALID_STAGES`` 内，否则视为未命中（None）。

    设计取舍：保持 best-effort，无路由 / 路由非法 → 返回 None，让 ``workflow_next``
    fallback 到默认 sequence + 1，向后兼容历史 decision.md。
    """
    import re as _re

    if not text:
        return None

    # 1) yaml frontmatter
    fm_match = _re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, _re.DOTALL)
    if fm_match:
        fm_body = fm_match.group(1)
        rt_match = _re.search(r"^\s*route_to\s*:\s*['\"]?([\w_-]+)['\"]?\s*$",
                              fm_body, _re.MULTILINE)
        if rt_match:
            candidate = rt_match.group(1).strip()
            if candidate in _REGRESSION_ROUTE_VALID_STAGES:
                return candidate

    # 2) 文本 marker：覆盖中文 "路由"/"路由动作" + 英文 "route"
    patterns = [
        r"路由\s*[:：=]\s*([\w_]+)",
        r"路由动作\s*[:：=]\s*[^\n]*?harness\s+next\s*[→\->\s]+([\w_]+)",
        r"harness\s+next\s*[→\->\s]+([\w_]+)",
        r"\broute\s*[:：=]\s*([\w_]+)",
    ]
    for pat in patterns:
        for m in _re.finditer(pat, text, _re.IGNORECASE):
            candidate = m.group(1).strip()
            if candidate in _REGRESSION_ROUTE_VALID_STAGES:
                return candidate
    return None


def _resolve_regression_route(root: Path, regression_id: str) -> str | None:
    """根据 regression id 定位 decision.md 并解析路由 stage。

    bugfix-3 / 缺陷 1：``workflow_next`` 入口若 ``current_regression`` 非空，调用本
    helper 优先消费 reg.decision 路由。未命中（无目录 / 无 decision.md / 文本无
    可识别路由）→ 返回 None，由调用方走默认 sequence。
    """
    if not regression_id:
        return None
    try:
        config = ensure_config(root)
    except SystemExit:
        return None
    reg_dir = _locate_regression_dir(root, regression_id, config["language"])
    if reg_dir is None:
        return None
    decision_path = reg_dir / "decision.md"
    if not decision_path.exists():
        return None
    try:
        text = decision_path.read_text(encoding="utf-8")
    except OSError:
        return None
    return _parse_decision_route(text)


def _render_key_details(details: dict) -> str:
    """req-38 / chg-03：把 pending details dict 拍平为简短可读字符串，用于 stderr 提示。

    例：{"provider": "apifox"} → "provider=apifox"
    """
    if not details:
        return ""
    return ", ".join(f"{k}={v}" for k, v in details.items())


# bugfix-5（同角色跨 stage 自动续跑硬门禁）：单一权威源 helper 组。
# 从 .workflow/context/role-model-map.yaml v2 schema 读 stages 字段，
# 构建"stage → role"反向索引，驱动 workflow_next 同角色连跳逻辑。

_ROLE_MODEL_MAP_PATH = Path(".workflow") / "context" / "role-model-map.yaml"

# v1 兼容：按角色名猜测默认覆盖 stage（与角色同名的 stage），未命中给空数组。
# req-50/chg-01: analyst now covers "analysis"; legacy stages kept for history archive read-only.
_V1_LEGACY_DEFAULT_STAGES: dict[str, list[str]] = {
    "analyst": ["analysis"],
    "executing": ["executing"],
    "testing": ["testing"],
    "acceptance": ["acceptance"],
    "regression": ["regression"],
    "done": ["done"],
    # legacy (req-id < 50, history archive read-only)
    "requirement-review": ["requirement_review"],
    "planning": ["planning"],
}

_ALL_VALID_STAGES = frozenset(
    set(WORKFLOW_SEQUENCE) | set(BUGFIX_SEQUENCE) | set(SUGGESTION_SEQUENCE)
)


def _load_role_stage_map(root: Path) -> dict:
    """从 role-model-map.yaml 加载完整 role 定义字典，含 v1 → v2 兼容转换。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）：
    - v2 格式（version: 2）：每个 role 已是 {model: ..., stages: [...]} dict，直接读。
    - v1 格式（version: 1）：每个 role 是 "model_name" 字符串，
      自动转 {model: ..., stages: [legacy_default]} 不报错；
      legacy_default 按 _V1_LEGACY_DEFAULT_STAGES 查，未命中给 []。
    返回值格式等价于 yaml["roles"] dict，已归一化为 v2 形态。
    """
    yaml_path = root / _ROLE_MODEL_MAP_PATH
    if not yaml_path.exists():
        return {}
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}

    version = raw.get("version", 1)
    roles_raw = raw.get("roles", {})
    if not isinstance(roles_raw, dict):
        return {}

    if version >= 2:
        # v2：各 role 已是 dict，直接返回（保护性处理：若遇到旧 string 条目也做兼容）
        normalized: dict[str, dict] = {}
        for role_name, role_def in roles_raw.items():
            if isinstance(role_def, str):
                # 混杂场景：v2 文件中仍有 string 条目
                normalized[role_name] = {
                    "model": role_def,
                    "stages": _V1_LEGACY_DEFAULT_STAGES.get(role_name, []),
                }
            elif isinstance(role_def, dict):
                normalized[role_name] = role_def
        return normalized
    else:
        # v1 兼容：string → dict
        normalized = {}
        for role_name, role_def in roles_raw.items():
            if isinstance(role_def, str):
                normalized[role_name] = {
                    "model": role_def,
                    "stages": _V1_LEGACY_DEFAULT_STAGES.get(role_name, []),
                }
            elif isinstance(role_def, dict):
                # v1 中混有 dict 形态（升级过渡期），直接保留
                normalized[role_name] = role_def
        return normalized


def _get_role_for_stage(stage: str, role_stage_map: dict) -> str | None:
    """反查 stage 对应的 role name。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）：
    - 命中多个时，优先返回非 alias（无 alias_of 字段）的主角色。
    - 全部为 alias → 返回第一个候选（兜底）。
    - 未命中（如 ready_for_execution 无角色直接覆盖）→ 返回 None，
      workflow_next 视为"角色边界"，正常逐格翻。
    """
    candidates = [
        role_name
        for role_name, role_def in role_stage_map.items()
        if isinstance(role_def, dict)
        and stage in role_def.get("stages", [])
        and not role_def.get("alias_of")  # 跳过 legacy alias
    ]
    return candidates[0] if candidates else None


def _load_stage_policies(root: Path) -> dict:
    """从 role-model-map.yaml 读取顶层 stage_policies 字段。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6：
    - 命中 stage_policies 字段 → 直接返回（dict[stage_name, dict]）。
    - 缺字段 / yaml 解析失败 → 返回 {}，调用方按 default 'user' 处理。
    """
    yaml_path = root / _ROLE_MODEL_MAP_PATH
    if not yaml_path.exists():
        return {}
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    policies = raw.get("stage_policies", {})
    if not isinstance(policies, dict):
        return {}
    return policies


def _get_exit_decision(stage: str, stage_policies: dict) -> str:
    """从 stage_policies 映射读取 stage 的 exit_decision。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6：
    - 命中 stage_policies[stage].exit_decision → 直接返回。
    - 未命中（yaml 未声明 / 桥接 stage 缺字段）→ 默认返回 'user'，
      保守起见把未知 stage 视为"需用户拍板"，避免误自动跳。
    """
    if not isinstance(stage_policies, dict):
        return "user"
    stage_policy = stage_policies.get(stage, {})
    if not isinstance(stage_policy, dict):
        return "user"
    return str(stage_policy.get("exit_decision", "user"))


def _is_stage_work_done(
    stage: str,
    root: Path,
    req_id: str,
    operation_type: str,
) -> bool:
    """检查 stage 的关键产物是否齐全。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    保守降级原则：所有无法解析的场景一律返回 True（不阻塞）。
    **例外**：executing stage 且 changes_dir 缺 / 无 session-memory.md 时返回 False
    （reg-02（over-chain 三维失配） + chg-02（保守降级严格化） 严格化：
    executing 出现在连跳链中时必须确实有 changes dir + session-memory.md 才视为 done）。

    检查规则：
    - testing：{req-flow-dir}/test-report.md 存在 + 含 §结论 / 结论
    - acceptance：{req-flow-dir}/acceptance/checklist.md 存在 + 含 §结论 / 结论
    - planning：≥ 1 个 chg-*/plan.md 存在 + 各含 §4 测试用例设计
    - executing（requirement/suggestion 模式）：changes 目录存在 + 每个 chg-*/session-memory.md 含 ✅，且 tests/ 下 ≥ 1 个 test_*.py
      - changes 目录缺 / 无 session-memory.md → False（严格化，不再保守降级）
    - executing（bugfix 模式）：req-flow/session-memory.md 存在 + 含 ✅，且 tests/ 下 ≥ 1 个 test_*.py
      （chg-07：bugfix 工件结构无 changes/ 子目录，按 operation_type 分路）
    - 其他 stage / 未知 stage / 解析失败 → True（保守降级）
    """
    # 保守降级：空 req_id / 未知 stage 直接返回 True
    if not req_id or not stage:
        return True
    _FALLBACK_STAGES = {
        "done", "regression", "analysis", "suggestion", "apply",
        # legacy (req-id < 50, history archive read-only)
        "requirement_review", "ready_for_execution", "planning",
    }
    if stage in _FALLBACK_STAGES:
        return True

    # 解析 flow 目录
    try:
        if operation_type == "bugfix":
            flow_base = root / ".workflow" / "flow" / "bugfixes"
        else:
            flow_base = root / ".workflow" / "flow" / "requirements"

        if not flow_base.exists():
            return True

        # 找 {req_id}-* 目录（操作符优先级修正：括号明确）
        matches = [
            d for d in flow_base.iterdir()
            if d.is_dir() and (d.name.startswith(f"{req_id}-") or d.name == req_id)
        ]
        if not matches:
            return True  # 找不到目录 → 保守降级

        req_flow = matches[0]

        def _has_conclusion_heading(text: str) -> bool:
            """检查文件是否含 §结论 或 ## 结论 / ## §结论 段落标题（而非普通文本中出现"结论"）。"""
            import re as _re
            return bool(_re.search(r"(?:^|\n)##\s*§?结论", text))

        if stage == "testing":
            # bugfix 模式产物是 test-evidence.md；requirement/suggestion 模式是 test-report.md
            # （与 chg-07 executing 分路同模式，bugfix 工件名不同）
            if operation_type == "bugfix":
                report = req_flow / "test-evidence.md"
            else:
                report = req_flow / "test-report.md"
            if not report.exists():
                return False
            content = report.read_text(encoding="utf-8")
            return _has_conclusion_heading(content)

        elif stage == "acceptance":
            checklist = req_flow / "acceptance" / "checklist.md"
            if not checklist.exists():
                return False
            content = checklist.read_text(encoding="utf-8")
            return _has_conclusion_heading(content)

        elif stage == "executing":
            if operation_type == "bugfix":
                # bugfix 模式：bugfix 工件结构无 changes/ 子目录；
                # 检查 bugfix-level session-memory.md 含 ✅
                # （chg-07：reg-02/chg-02 严格化遗漏 bugfix 路径修复）
                sm = req_flow / "session-memory.md"
                if not sm.exists():
                    return False
                content = sm.read_text(encoding="utf-8")
                if "✅" not in content:
                    return False
            else:
                # requirement / suggestion 模式：原有逻辑
                # 每个 chg-*/session-memory.md 末尾含 ✅
                changes_dir = req_flow / "changes"
                if not changes_dir.exists():
                    # 严格化（reg-02（over-chain 三维失配） + chg-02（保守降级严格化））：
                    # executing 但无 changes 目录 = subagent 还没派发 = work 未做，应阻断 next 自动连跳
                    return False
                sm_files = list(changes_dir.glob("*/session-memory.md"))
                if not sm_files:
                    # 严格化（reg-02（over-chain 三维失配） + chg-02（保守降级严格化））：
                    # changes 目录存在但无任何 session-memory.md = subagent 还没完成 = work 未做
                    return False
                for sm in sm_files:
                    content = sm.read_text(encoding="utf-8")
                    if "✅" not in content:
                        return False
            # tests/ 下至少 1 个 test_*.py（两模式共用）
            tests_dir = root / "tests"
            if tests_dir.exists():
                test_files = list(tests_dir.glob("test_*.py"))
                if not test_files:
                    return False
            return True

        # 其他未知 stage → 保守降级
        return True

    except Exception:
        return True  # 任何异常 → 保守降级


def workflow_next(root: Path, execute: bool = False) -> int:
    runtime = load_requirement_runtime(root)

    # req-38 / chg-03：pending gate——stage_pending_user_action 非空时拒绝推进。
    # gate 置于 stage 切换逻辑最前，确保 stage_history 不追加、stage_entered_at 不刷新。
    pending = runtime.get("stage_pending_user_action")
    if isinstance(pending, dict) and pending:
        typ = pending.get("type", "unknown")
        key_details = _render_key_details(pending.get("details", {}))
        detail_str = f"（{key_details}）" if key_details else ""
        print(
            f"stage 正在等待 {typ}{detail_str}，请完成用户动作后再次 harness next",
            file=sys.stderr,
        )
        return 3

    current_stage = str(runtime.get("stage", "")).strip()
    operation_type = str(runtime.get("operation_type", "")).strip()

    # 根据 operation_type 选择对应的 stage 序列
    # upstream-fix: legacy stages（requirement_review / planning / ready_for_execution）
    # 属于 req-id < 50 的旧工作流序列，必须用 LEGACY_WORKFLOW_SEQUENCE 处理。
    if operation_type == "bugfix":
        sequence = BUGFIX_SEQUENCE
    elif operation_type == "suggestion":
        sequence = SUGGESTION_SEQUENCE
    elif operation_type == "trivial":
        sequence = TRIVIAL_SEQUENCE
    elif current_stage in ("requirement_review", "planning", "ready_for_execution"):
        # legacy req (req-id < 50) — use legacy sequence
        sequence = LEGACY_WORKFLOW_SEQUENCE
    else:
        sequence = WORKFLOW_SEQUENCE

    if not current_stage:
        raise SystemExit("No active workflow stage. Run `harness requirement <title>` to begin.")

    # bugfix-3 / 缺陷 1（sug-12 复发）：若 current_regression 非空，优先读
    # decision.md 路由覆盖默认 sequence + 1。命中后清空 current_regression，
    # 防止下次 next 重复消费同一 regression 决策。
    # 路由检查放到 sequence 校验之前，让"主线已 done 但 reg 决定回到 planning"
    # 这种场景也能走通（否则 done 触发 SystemExit）。
    current_regression = str(runtime.get("current_regression", "")).strip()
    routed_stage_from_reg: str | None = None
    if current_regression:
        routed_stage_from_reg = _resolve_regression_route(root, current_regression)

    if routed_stage_from_reg is None:
        # 无 reg 路由 → 走原校验
        if current_stage == "done":
            raise SystemExit("Workflow is already complete.")
        if current_stage not in sequence:
            raise SystemExit(f"Unknown stage: {current_stage}")
        idx = sequence.index(current_stage)
        # legacy gate for old reqs (req-id < 50)
        if current_stage == "ready_for_execution" and not execute:
            raise SystemExit("Workflow is ready_for_execution. Run `harness next --execute` to confirm execution start.")
        next_stage = sequence[idx + 1] if idx + 1 < len(sequence) else current_stage
    else:
        # reg 路由命中：直接采用，跳过 sequence 校验（允许 done → planning 等回退）
        next_stage = routed_stage_from_reg
        runtime["current_regression"] = ""
        runtime["current_regression_title"] = ""

    # req-26 / chg-03（AC-03）：state yaml 双写同步 — 解析 operation_target 供后续使用。
    # 回退顺序：operation_target → current_requirement。保证 stage 推进必写。
    operation_target = str(runtime.get("operation_target", "")).strip()
    if not operation_target:
        operation_target = str(runtime.get("current_requirement", "")).strip()

    # bugfix-5（同角色跨 stage 自动续跑硬门禁）：同角色连跳 + verdict-driven 连跳逻辑。
    # 从权威源 role-model-map.yaml 加载 stage→role 映射 + stage_policies。
    # 策略：把"从 current_stage 开始的所有连跳格（含最终落点）"都写一遍事件 + state，
    # 每格独立写，不合并，确保 done 阶段六层回顾 stage_timestamps 数据完整。
    # reg 路由命中（routed_stage_from_reg is not None）时不参与连跳。
    role_stage_map = _load_role_stage_map(root)
    current_role_for_advance = _get_role_for_stage(current_stage, role_stage_map)
    # 修复点 6：加载 stage_policies，驱动 verdict-driven / auto-driven 连跳
    stage_policies = _load_stage_policies(root)
    # auto / verdict 类型出口触发连跳；explicit / user / terminal 停下
    _AUTO_JUMP_DECISIONS = {"auto", "verdict"}

    def _write_stage_transition(from_s: str, to_s: str, prev_iso: str) -> None:
        """写单格 stage 跳转：events + runtime + state yaml + stdout。"""
        dur: float | None = None
        if prev_iso:
            try:
                dur = (datetime.now(timezone.utc) - datetime.fromisoformat(prev_iso)).total_seconds()
            except (ValueError, TypeError):
                pass
        record_feedback_event(root, "stage_duration", {
            "stage": from_s,
            "duration_seconds": dur if dur is not None else 0,
        })
        record_feedback_event(root, "stage_advance", {"from_stage": from_s, "to_stage": to_s})
        runtime["stage"] = to_s
        runtime["stage_entered_at"] = datetime.now(timezone.utc).isoformat()
        _reset_ff_mode_after_done_archive(runtime, to_s)
        _sync_stage_to_state_yaml(root, operation_type, operation_target, to_s)
        save_requirement_runtime(root, runtime)
        print(f"Workflow advanced to {to_s}")

    # req-50/chg-01: analyst stage 退出门禁：analysis → executing 流转前跑 artifact-placement lint；FAIL 则阻塞流转
    # req-46: legacy gates for old reqs (requirement_review → planning / planning → ready_for_execution)
    _ANALYST_GATE_STAGES = {"analysis", "requirement_review", "planning"}
    if (
        routed_stage_from_reg is None
        and current_stage in _ANALYST_GATE_STAGES
        and current_stage in sequence
    ):
        from harness_workflow.validate_contract import check_artifact_placement as _wf_check_ap  # noqa: PLC0415
        _ap_lint_result = _wf_check_ap(root)
        if _ap_lint_result != 0:
            print(
                f"ABORT: artifact-placement lint FAIL — {current_stage} 退出门禁阻塞流转。"
                " 请先修复 artifacts/ 下机器型文件位置，再重试 `harness next`。",
                file=sys.stderr,
            )
            return 1

    if routed_stage_from_reg is None and current_stage in sequence:
        # 同角色连跳 + verdict-driven 连跳路径（修复点 2 + 修复点 6 合并）：
        # 1) 首先写出 current_stage → next_stage（第一格，已由上方逻辑确定）
        # 2) 若当前 stage 出口决策为 auto/verdict，或下一 stage 同角色，继续连跳
        # 3) explicit / user / terminal 出口永远停下
        from_s = current_stage
        prev_iso = str(runtime.get("stage_entered_at", ""))
        to_s = next_stage
        walk_idx = sequence.index(next_stage) if next_stage in sequence else -1

        # req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
        # BUG-01 修复：第一格转换前的 work-done gate。
        # 检查出发 stage 的产物是否齐全；same_role 路径豁免（保 bugfix-5（同角色跨 stage 自动续跑硬门禁） 契约）。
        _first_hop_exit = _get_exit_decision(current_stage, stage_policies)
        _next_role = _get_role_for_stage(next_stage, role_stage_map)
        _first_hop_same_role = (
            current_role_for_advance is not None
            and _next_role == current_role_for_advance
        )
        if (
            _first_hop_exit in _AUTO_JUMP_DECISIONS
            and not _first_hop_same_role
            and not _is_stage_work_done(current_stage, root, operation_target, operation_type)
        ):
            print(
                f"Stage {current_stage} 工作未完成，请先完成当前阶段工作再推进。",
                file=sys.stderr,
            )
            return 0

        _write_stage_transition(from_s, to_s, prev_iso)
        from_s = to_s
        prev_iso = str(runtime.get("stage_entered_at", ""))

        # 继续连跳（同角色 OR exit_decision in {auto, verdict}，但 explicit 永远停下）
        while walk_idx >= 0 and walk_idx + 1 < len(sequence):
            # 读取"已落点 from_s"的出口决策（注意：每翻一格，from_s 更新为新的当前格）
            current_exit = _get_exit_decision(from_s, stage_policies)
            # explicit 出口：永远停下，即使其他条件成立
            if current_exit == "explicit":
                break
            candidate = sequence[walk_idx + 1]
            candidate_role = _get_role_for_stage(candidate, role_stage_map)
            # 同角色条件（修复点 2 原逻辑）
            same_role = (
                current_role_for_advance is not None
                and candidate_role == current_role_for_advance
            )
            # verdict-driven / auto-driven 条件（修复点 6 新逻辑）
            no_user_decision = current_exit in _AUTO_JUMP_DECISIONS
            if not (same_role or no_user_decision):
                break
            # req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
            # while 内 work-done gate：防多格连跳；same_role 路径豁免（bugfix-5（同角色跨 stage 自动续跑硬门禁） 契约）
            if no_user_decision and not same_role and not _is_stage_work_done(from_s, root, operation_target, operation_type):
                break
            _write_stage_transition(from_s, candidate, prev_iso)
            from_s = candidate
            prev_iso = str(runtime.get("stage_entered_at", ""))
            walk_idx += 1
            next_stage = candidate  # 最终落点持续更新
    else:
        # 无连跳路径（reg 路由命中 / 非 sequence 内 stage）：
        # 沿用原有单格写逻辑。
        prev_entered_at = str(runtime.get("stage_entered_at", ""))
        _write_stage_transition(current_stage, next_stage, prev_entered_at)

    if next_stage == "done" and operation_target:
        extract_suggestions_from_done_report(root, operation_target)
        print("Review `context/experience/stage/` and update relevant stage experience before archiving.")

    # req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 6（sug-09）：
    # --execute 派发 subagent briefing 供主 agent 直接消费，不仅翻 stage 字段。
    # req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO
    # 派发 briefing 注入 task_context_index + 快照落盘）：先构建索引 → 写快照 →
    # 注入 briefing 两字段，向后兼容未传 index 的调用方。
    if execute and next_stage not in _NO_BRIEFING_STAGES:
        req_title = str(runtime.get("current_requirement_title", "")).strip()
        if not req_title and operation_target:
            req_title = _resolve_title_for_id(root, operation_target) or ""
        idx_list: list[dict] = []
        idx_rel: str = ""
        if operation_target:
            idx_list = _build_task_context_index(
                root=root, stage=next_stage, req_id=operation_target
            )
            snap = _write_task_context_snapshot(
                root=root, req_id=operation_target, stage=next_stage, index=idx_list
            )
            try:
                idx_rel = str(snap.relative_to(root))
            except ValueError:
                idx_rel = str(snap)
        briefing = _build_subagent_briefing(
            next_stage,
            operation_target or "",
            req_title,
            task_context_index=idx_list,
            task_context_index_file=idx_rel,
        )
        print(briefing)
    return 0


def workflow_fast_forward(root: Path) -> int:
    runtime = load_requirement_runtime(root)
    from_stage = str(runtime.get("stage", "")).strip()
    operation_type = str(runtime.get("operation_type", "")).strip()
    operation_target = str(runtime.get("operation_target", "")).strip()

    # 根据 operation_type 确定目标 stage
    # req-50/chg-01: ff 跳到 executing（新 5-stage 无 ready_for_execution）
    if operation_type == "bugfix":
        target_stage = "executing"
    elif operation_type == "suggestion":
        target_stage = "apply"
    else:
        target_stage = "executing"  # req-50/chg-01: was ready_for_execution

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
    # req-30 / chg-02（AC-03）：ff 主循环打印 stage 切换信息时附带当前工作项 title，
    # 方便跨 agent 协作读 stdout 即知目标。
    if operation_target:
        rendered_target = render_work_item_id(operation_target, runtime=runtime, root=root)
        print(f"Workflow advanced to {target_stage} for {rendered_target}")
    else:
        print(f"Workflow advanced to {target_stage}")
    return 0


def enter_workflow(root: Path, req_id: str = "") -> int:
    runtime = load_requirement_runtime(root)
    if req_id:
        runtime["current_requirement"] = req_id
        # req-30 / chg-01：id 变更时同步 *_title 缓存，subagent 进入 harness 模式后读 runtime
        # 即可拿到 title（场景 4：briefing 无需二次查文件）。
        runtime["current_requirement_title"] = _resolve_title_for_id(root, req_id)
        # bugfix-3 / 缺陷 2（sug-13 复发）：切换 id 时强制重设 operation_type /
        # operation_target，避免上次 req-X 的残留值导致 _sync_stage_to_state_yaml
        # 写到错误的子目录（requirement→bugfix 切换后 stage 写不进 bugfix yaml）。
        if req_id.startswith("bugfix-"):
            runtime["operation_type"] = "bugfix"
        elif req_id.startswith("sug-"):
            runtime["operation_type"] = "suggestion"
        else:
            runtime["operation_type"] = "requirement"
        runtime["operation_target"] = req_id
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
        "claude": root / ".claude" / "skills" / "harness",
        "cc": root / ".claude" / "skills" / "harness",
        "codex": root / ".codex" / "skills" / "harness",
    }
    return agent_dir_map.get(agent, root / f".{agent}" / "skills" / "harness")


def install_agent(root: Path, agent: str) -> int:
    """Install harness skill to target agent directory.

    Args:
        root: Repository root
        agent: Target agent (cc, claude, codex)

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
            write_agents=(agent in ("codex",)),
            write_claude=(agent in ("claude", "cc")),
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

    # bugfix-3（新）问题 1：持久化当前选定 agent，供后续 update_repo 感知作用域。
    try:
        write_active_agent(root, agent)
    except Exception as exc:  # noqa: BLE001
        # 持久化失败不应中断 install（已完成的 skill 安装有效），打印警告即可
        print(f"Warning: failed to persist active_agent={agent} to platforms.yaml: {exc}")

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


def _install_self_audit(root: Path) -> int:
    """req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2 mirror 保持一致））/
    chg-02 + chg-06（解锁 _install_self_audit 触发面）：
    install 末尾自检 helper。chg-02 落地时锁在本仓库自身（pyproject.toml `name = "harness-workflow"`
    锚点）；chg-06 删除 pyproject 锚点段，触发面默认全开（任何 install 都跑），仅保留
    ``HARNESS_DEV_REPO_ROOT`` env 作开发期 escape hatch（env 设置 + 路径不匹配时跳过）。

    req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）注：
    本 helper "反向：live 多出 mirror 没有的非白名单文件" 分支（约第 8152 行）只扫 `.workflow/`，
    天然不扫 `artifacts/`；项目级三类目录在 artifacts/ 下，故无需在本 helper 内单独豁免。
    `_SCAFFOLD_V2_MIRROR_WHITELIST` 含 "artifacts/project/" + "/project/" 双条目（req-52 / chg-02 改），
    用于 `_sync_scaffold_v2_mirror_to_live` 的反向清理 stale_keys 分支兜底。
    （req-52 / chg-02：原注释的旧路径已迁移为 artifacts/project/ 主路径，legacy 由 /project/ 兜底）

    返回：drift 计数。命中差异时 stderr 逐条 + 末尾 WARNING；零差异时静默 return 0。
    """
    # 1) 触发面判定（仅保留 env-based escape hatch；pyproject 锚点已由 chg-06 删除）
    dev_root_env = os.environ.get("HARNESS_DEV_REPO_ROOT")
    if dev_root_env and Path(dev_root_env).resolve() != root.resolve():
        return 0

    # 2) 白名单复用 chg-05 抽出的模块级常量 _SCAFFOLD_V2_MIRROR_WHITELIST
    whitelist_substrings = _SCAFFOLD_V2_MIRROR_WHITELIST

    # 3) live vs mirror diff（mirror 全量 dict）
    mirror = _scaffold_v2_file_contents(root, include_agents=False, include_claude=False, language="cn")
    drift_count = 0
    for relative, expected in mirror.items():
        if any(w in relative for w in whitelist_substrings):
            continue
        live_path = root / relative
        if not live_path.exists():
            print(f"[install_repo:self-audit] drift detected (missing in live): {relative}", file=sys.stderr)
            drift_count += 1
            continue
        actual = live_path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"[install_repo:self-audit] drift detected (content differs): {relative}", file=sys.stderr)
            drift_count += 1

    # 4) 反向：live 多出 mirror 没有的非白名单文件
    live_workflow = root / ".workflow"
    if live_workflow.exists():
        for live_path in sorted(live_workflow.rglob("*")):
            if not live_path.is_file():
                continue
            relative = live_path.relative_to(root).as_posix()
            if any(w in relative for w in whitelist_substrings):
                continue
            if relative not in mirror:
                print(f"[install_repo:self-audit] drift detected (only in live): {relative}", file=sys.stderr)
                drift_count += 1

    if drift_count > 0:
        # Fix-A chg-01：drift > 0 时必须强提示（不可静默）；
        # 用 \033[33m...\033[0m ANSI 黄色标注 WARNING，让用户在 stderr 中明显感知。
        print(
            f"\033[33m[install_repo:self-audit] WARNING: {drift_count} drift(s) detected; "
            f"pass --force-managed to overwrite, or see {root}/.workflow/audit.md\033[0m",
            file=sys.stderr,
        )
    return drift_count


# ---------------------------------------------------------------------------
# req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
# / chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）
# HARNESS_BLOCK 错误协议 helper
# ---------------------------------------------------------------------------

def raise_harness_block(
    error_type: str,
    fix_checklist_path: str,
    retry_context: dict,
    severity: str = "FAIL",
    detected_by: str = "executing",
    root: Optional[Path] = None,
) -> int:
    """发出 HARNESS_BLOCK 协议信号，写 runtime-block.yaml，返回 exit code。

    三层载体：
    1. stderr：HARNESS_BLOCK: {error_type} + fix-checklist: ... + severity: ...
    2. exit code：FAIL=64, ABORT=65, WARN=0
    3. .workflow/state/runtime-block.yaml：结构化状态文件

    Args:
        error_type: 已知错误类型（artifact-placement / schema-audit / missing-document / ...）
        fix_checklist_path: fix-checklist 文件路径（相对或绝对）
        retry_context: 重试上下文字典（任意键值，存入 yaml）
        severity: FAIL | ABORT | WARN
        detected_by: 发现阶段（executing / testing / reviewing / ...）
        root: 项目根目录（默认 Path('.')）

    Returns:
        int: 64（FAIL）/ 65（ABORT）/ 0（WARN）
    """
    _VALID_SEVERITIES = ("FAIL", "ABORT", "WARN")
    if severity not in _VALID_SEVERITIES:
        raise ValueError(f"severity must be FAIL/ABORT/WARN, got: {severity!r}")

    if root is None:
        root = Path(".")

    # 1) stderr 输出 HARNESS_BLOCK 协议
    print(f"HARNESS_BLOCK: {error_type}", file=sys.stderr)
    print(f"  fix-checklist: {fix_checklist_path}", file=sys.stderr)
    print(f"  severity: {severity}", file=sys.stderr)
    print(f"  detected-by: {detected_by}", file=sys.stderr)

    # 2) 写 runtime-block.yaml（recovery_attempts 累加）
    block_path = root / ".workflow" / "state" / "runtime-block.yaml"
    block_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict = {}
    if block_path.exists():
        try:
            existing = yaml.safe_load(block_path.read_text(encoding="utf-8")) or {}
        except Exception:
            existing = {}

    # recovery_attempts 同 error_type 时累加，换 type 时重置
    if existing.get("error_type") == error_type:
        attempts = int(existing.get("recovery_attempts", 0)) + 1
    else:
        attempts = 1

    block_data = {
        "error_type": error_type,
        "fix_checklist_path": fix_checklist_path,
        "retry_context": retry_context,
        "severity": severity,
        "detected_by": detected_by,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "recovery_attempts": attempts,
    }

    block_path.write_text(
        yaml.dump(block_data, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )

    # 3) 返回 exit code
    if severity == "ABORT":
        return 65
    elif severity == "WARN":
        return 0
    else:  # FAIL
        return 64


def _merge_project_level_files(
    global_dir: Path,
    project_dir: Path,
) -> dict[str, Path]:
    """req-51（项目级规则-经验-工具支持从制品引入）/ chg-03（加载层覆盖-tools-项目级合并）+
    req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-04（接入主流程-stderr日志-端到端CLI验证）：
    把全局子树与项目级子树按 basename 合并，同名时项目级覆盖全局。

    返回：dict[basename, Path]，basename 为相对 global_dir / project_dir 的路径字符串。

    fallback：
    - global_dir 不存在 → 仅返回 project_dir 内容（如有）；
    - project_dir 不存在 → 仅返回 global_dir 内容（向后兼容）；
    - 两者都不存在 → 返回 {}。

    集成（chg-04 落地）：
    - 由 install_repo / update_repo 入口段调用（line ~3791 区域），对三个 scope 大类
      （constraints / experience / tools）逐个触发探测；结果通过 _log_project_level_load 输出 stderr。
    - 加载链消费：role-loading-protocol Step 7.6 / 7.6.1（chg-03 索引懒加载）+ tools-manager Step 2.0。
    """
    merged: dict[str, Path] = {}
    if global_dir.exists():
        for f in global_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(global_dir).as_posix()
                merged[rel] = f
    if project_dir.exists():
        for f in project_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(project_dir).as_posix()
                merged[rel] = f  # 同名覆盖全局
    return merged


def _log_project_level_load(
    root: Path,
    scope: str,
    hits: int,
    fallback_used: bool,
) -> None:
    """req-52 / chg-04：项目级加载链 stderr 日志输出 helper。

    格式：[harness] project-level loaded: {N} files from {path}（fallback={legacy_path or "n/a"}）

    入参：
    - root: 项目根目录
    - scope: ∈ {"constraints", "experience", "tools"}
    - hits: 命中文件数
    - fallback_used: 是否走了 legacy 路径（artifacts/{branch}/project/）

    行为：仅写 stderr，不写盘；e2e pytest 断言依赖此格式（OQ-C = A）。
    """
    # 主路径（chg-01 OQ-A 主路径）
    main_path = f"artifacts/project/{scope}/"
    if fallback_used:
        branch = _get_git_branch(root) or "main"
        legacy_path = f"artifacts/{branch}/project/{scope}/"
        msg = (
            f"[harness] project-level loaded: {hits} files from {legacy_path}"
            f"（fallback=主路径 {main_path} 不存在）"
        )
    else:
        msg = (
            f"[harness] project-level loaded: {hits} files from {main_path}"
            f"（fallback=n/a）"
        )
    print(msg, file=sys.stderr)


def _load_project_level_index(
    root: Path,
    scope: str,
) -> list[dict]:
    """req-52（硬编码main路径全面去除-跟项目走-索引懒加载-流程日志验证）/ chg-03（索引懒加载-index-md与加载链改造）：
    解析项目级子目录 index.md，返回清单（不读取条目内容，由 agent 按 when_load 决定是否加载）。

    入参：
    - root: 项目根目录
    - scope: ∈ {"constraints", "experience-roles", "experience-tool", "experience-risk",
                "experience-regression", "experience-stage"}

    行为：
    1. 主路径 = artifacts/project/{scope_subpath}/index.md（chg-01 主路径，无 branch）
    2. branch-path 兼容路径 = artifacts/{branch}/project/{scope_subpath}/index.md（chg-01 双轨过渡）
    3. 解析 markdown 表格，提取 (path, title, scope, when_load) 四字段；
    4. 主路径 + legacy 均不存在 → 返回 []（agent fallback 到全量 rglob）。

    返回：list[dict]，每项含 {"path", "title", "scope", "when_load", "source"}（source ∈ "main" | "legacy"）。
    """
    # scope → 子目录映射
    scope_map = {
        "constraints": Path("constraints"),
        "experience-roles": Path("experience") / "roles",
        "experience-tool": Path("experience") / "tool",
        "experience-risk": Path("experience") / "risk",
        "experience-regression": Path("experience") / "regression",
        "experience-stage": Path("experience") / "stage",
    }
    if scope not in scope_map:
        return []
    sub = scope_map[scope]

    # 主路径优先（chg-01 OQ-A 主路径，无 branch）
    main_idx = root / "artifacts" / "project" / sub / "index.md"
    if main_idx.is_file():
        return _parse_index_md(main_idx, source="main")

    # branch-path 兼容路径（chg-01 双轨过渡）
    branch = _get_git_branch(root) or "main"
    legacy_idx = root / "artifacts" / branch / "project" / sub / "index.md"
    if legacy_idx.is_file():
        return _parse_index_md(legacy_idx, source="legacy")

    return []


def _parse_index_md(idx_path: Path, source: str) -> list[dict]:
    """解析 index.md markdown 表格，返回 list[dict]。仅取 (path, title, scope, when_load) 4 字段。"""
    try:
        text = idx_path.read_text(encoding="utf-8")
    except OSError:
        return []
    rows: list[dict] = []
    in_table = False
    for line in text.splitlines():
        s = line.strip()
        # 表头识别
        if s.startswith("| path") and "title" in s and "scope" in s:
            in_table = True
            continue
        if in_table and s.startswith("|---"):
            continue  # 分隔行
        if in_table:
            if not s.startswith("|"):
                in_table = False  # 表格结束
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) < 4:
                continue
            path_cell, title_cell, scope_cell, when_load_cell = cells[0], cells[1], cells[2], cells[3]
            # 跳过示例占位行（含 HTML 注释）
            if "<!--" in path_cell or not path_cell:
                continue
            rows.append({
                "path": path_cell,
                "title": title_cell,
                "scope": scope_cell,
                "when_load": when_load_cell,
                "source": source,
            })
    return rows


# ============================================================
# req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）
# chg-01: CLI 入口 + 反非法 lint helpers（stub → chg-02/03/04 替换）
# chg-02: _pad_add 真实落位 + _resolve_pad_target
# chg-03: index.md 登记 + git auto-stage + 加载链活证
# chg-04: _pad_list / _pad_interactive 真实实现 + _parse_tool_list_section
# ============================================================

def _validate_pad_kind(kind: str) -> str | None:
    """非法 kind → 返回错误信息字符串；合法 → 返回 None。"""
    if kind not in PAD_KINDS:
        return "kind 必须是 rule/experience/tool 之一"
    return None


def _validate_pad_scope(kind: str, scope: str) -> str | None:
    """非法 scope → 返回错误信息字符串；合法 → 返回 None。
    tool 不分 scope，传任何 scope 都报错（除非空字符串）。
    rule / experience：scope 必须在白名单内。

    错误信息模板（按 kind 分类，保证 grep 可测）：
    - rule:       "rule scope 必须是 coding/architecture/api/database/security 之一"
    - experience: "experience scope 必须是 roles/stage/regression/risk/tool 之一"
    """
    if kind == "tool":
        if scope:
            return "tool 不分 scope，请直接 `harness pad tool <title>`"
        return None
    allowed = PAD_KINDS.get(kind, [])
    if scope not in allowed:
        allowed_str = "/".join(allowed)
        # 错误信息含 `{kind} scope 必须是 ...` 字面串，供 lint grep 校验
        # rule scope 必须是 coding/architecture/api/database/security 之一
        # experience scope 必须是 roles/stage/regression/risk/tool 之一
        return f"{kind} scope 必须是 {allowed_str} 之一"
    return None


def _resolve_pad_target(root: Path, kind: str, scope: str, slug: str) -> "Path | None":
    """req-53 / chg-02：按 kind + scope + slug 算 artifacts/project/ 下的目标文件路径。

    - kind=rule → artifacts/project/constraints/{scope}/{slug}.md
    - kind=experience → artifacts/project/experience/{scope}/{slug}.md
    - kind=tool → artifacts/project/tools/{slug}.md
    """
    base = root / "artifacts" / "project"
    if kind == "rule":
        if not scope:
            return None
        return base / "constraints" / scope / f"{slug}.md"
    if kind == "experience":
        if not scope:
            return None
        return base / "experience" / scope / f"{slug}.md"
    if kind == "tool":
        return base / "tools" / f"{slug}.md"
    return None


def _append_table_row(idx_path: Path, new_row: str) -> "Path | None":
    """往 markdown 表格 index.md 末尾追加一行；若表头不存在自动补齐。

    幂等：如果 new_row 已存在则不再追加。
    """
    if not idx_path.parent.exists():
        idx_path.parent.mkdir(parents=True, exist_ok=True)
    if not idx_path.exists():
        # 创建带表头的 index.md
        idx_path.write_text(
            f"| path | title | scope | when_load | 备注 |\n"
            f"|------|-------|-------|-----------|------|\n"
            f"{new_row}\n",
            encoding="utf-8",
        )
        return idx_path
    text = idx_path.read_text(encoding="utf-8")
    # 幂等：若 new_row 已存在 skip
    if new_row.strip() in text:
        return idx_path
    lines = text.splitlines()
    # 找表头位置
    header_idx = -1
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("| path") and "title" in s and "scope" in s:
            header_idx = i
            break
    if header_idx == -1:
        # 表头缺失 → 在文件末尾补全表
        lines.append("")
        lines.append("| path | title | scope | when_load | 备注 |")
        lines.append("|------|-------|-------|-----------|------|")
        lines.append(new_row)
    else:
        # 找表格末尾（第一个不以 | 开头的行）
        end_idx = len(lines)
        for j in range(header_idx + 2, len(lines)):  # +2 跳过表头 + 分隔行
            if not lines[j].strip().startswith("|"):
                end_idx = j
                break
        lines.insert(end_idx, new_row)
    idx_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return idx_path


def _append_tool_list_item(idx_path: Path, new_line: str) -> "Path | None":
    """往 tools/index.md「## 项目级工具清单」段末追加列表项；段不存在则创建。

    幂等：如果 new_line 已存在则不再追加。
    """
    if not idx_path.parent.exists():
        idx_path.parent.mkdir(parents=True, exist_ok=True)
    if not idx_path.exists():
        idx_path.write_text(
            f"# Project-level Tools Index\n\n## 项目级工具清单\n\n{new_line}\n",
            encoding="utf-8",
        )
        return idx_path
    text = idx_path.read_text(encoding="utf-8")
    if new_line.strip() in text:
        return idx_path
    if "## 项目级工具清单" not in text:
        # 段不存在 → 文件末尾追加段
        if not text.endswith("\n"):
            text += "\n"
        text += f"\n## 项目级工具清单\n\n{new_line}\n"
    else:
        lines = text.splitlines()
        section_idx = -1
        for i, line in enumerate(lines):
            if line.strip() == "## 项目级工具清单":
                section_idx = i
                break
        # 找段末尾（下一个 ## 标题或文件末尾）
        end_idx = len(lines)
        for j in range(section_idx + 1, len(lines)):
            if lines[j].startswith("## "):
                end_idx = j
                break
        # 段尾插入新列表项
        lines.insert(end_idx, new_line)
        text = "\n".join(lines) + "\n"
    idx_path.write_text(text, encoding="utf-8")
    return idx_path


def _pad_register_index(root: Path, kind: str, scope: str, slug: str, title: str) -> "Path | None":
    """req-53 / chg-03：往对应 index.md 追加新条目，按 kind schema 分类。

    - kind=rule → artifacts/project/constraints/index.md 表格末追加
                  `| {scope}/{slug}.md | {title} | {scope} | always | (空) |`
    - kind=experience → artifacts/project/experience/{scope}/index.md 表格末追加
                  `| {slug}.md | {title} | experience-{scope} | always | (空) |`
    - kind=tool → artifacts/project/tools/index.md「## 项目级工具清单」段末追加 `- {slug}.md — {title}`

    返回：被修改的 index.md 路径（用于 git add）；解析失败返回 None。
    """
    base = root / "artifacts" / "project"
    if kind == "rule":
        idx = base / "constraints" / "index.md"
        new_row = f"| {scope}/{slug}.md | {title} | {scope} | always | (空) |"
        return _append_table_row(idx, new_row)
    if kind == "experience":
        idx = base / "experience" / scope / "index.md"
        new_row = f"| {slug}.md | {title} | experience-{scope} | always | (空) |"
        return _append_table_row(idx, new_row)
    if kind == "tool":
        idx = base / "tools" / "index.md"
        new_line = f"- {slug}.md — {title}"
        return _append_tool_list_item(idx, new_line)
    return None


def _pad_git_stage(root: Path, paths: "list[Path]") -> bool:
    """req-53 / chg-03：调 git add 把指定路径加入 stage。

    返回：True = 全部成功；False = 任一失败 / 非 git 仓 / git 缺失。
    失败时 stderr 警告但不抛异常（OQ-5 决策：silent skip 不阻塞）。
    """
    import subprocess as _subprocess
    if not (root / ".git").exists():
        print("[harness pad] (info) 非 git 仓，跳过 git add", file=sys.stderr)
        return False
    try:
        for p in paths:
            rel = p.relative_to(root).as_posix()
            result = _subprocess.run(
                ["git", "add", rel],
                cwd=str(root),
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(
                    f"[harness pad] (warn) git add {rel} failed: {result.stderr.strip()}",
                    file=sys.stderr,
                )
                return False
        return True
    except FileNotFoundError:
        print("[harness pad] (warn) git 命令缺失，跳过 git add", file=sys.stderr)
        return False


def _parse_tool_list_section(idx_path: Path) -> "list[str]":
    """req-53 / chg-04：解析 tools/index.md「## 项目级工具清单」段下的 markdown 列表项。
    返回去掉前缀 `- ` 后的字符串列表。
    """
    if not idx_path.is_file():
        return []
    text = idx_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    section_idx = -1
    for i, line in enumerate(lines):
        if line.strip() == "## 项目级工具清单":
            section_idx = i
            break
    if section_idx < 0:
        return []
    items: list[str] = []
    for j in range(section_idx + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith("## "):
            break  # 段结束
        if s.startswith("- "):
            items.append(s[2:])
    return items


def _pad_add(root: Path, kind: str, scope: str, title: str) -> int:
    """req-53 / chg-02 + chg-03：把条目落到 artifacts/project/{kind}/{scope}/{slug}.md。

    - kind=rule → artifacts/project/constraints/{scope}/{slug}.md
    - kind=experience → artifacts/project/experience/{scope}/{slug}.md
    - kind=tool → artifacts/project/tools/{slug}.md
    - slug 由 title 经 _path_slug 转换
    - 渲染对应 .tmpl 模板（assets/templates/project-add/{kind}.md.tmpl）
    - 调 write_if_missing 写盘（幂等，不覆盖）
    - chg-03：追加 index.md 登记 + git auto-stage + 加载链 stderr 活证
    """
    from datetime import date
    slug = _path_slug(title) or title  # _path_slug 退化到 title 本身（CN 场景保留中文）
    target = _resolve_pad_target(root, kind, scope, slug)
    if target is None:
        print(f"[harness pad] ABORT: 无法解析路径 kind={kind} scope={scope}", file=sys.stderr)
        return 2

    # 模板渲染
    tmpl_path = PACKAGE_FS_ROOT / "assets" / "templates" / "project-add" / f"{kind}.md.tmpl"
    if not tmpl_path.exists():
        print(f"[harness pad] ABORT: 模板缺失 {tmpl_path}", file=sys.stderr)
        return 2
    content = tmpl_path.read_text(encoding="utf-8")
    content = content.replace("{{ slug }}", slug)
    content = content.replace("{{ scope }}", scope or "tools")  # tool kind 写 tools
    content = content.replace("{{ title }}", title)
    content = content.replace("{{ created_at }}", date.today().isoformat())

    # 写盘（幂等）
    created: list[str] = []
    skipped: list[str] = []
    write_if_missing(target, content, created, skipped)
    rel = target.relative_to(root).as_posix()
    if created:
        print(f"[harness pad] added {rel} ✓")
    else:
        print(f"[harness pad] {rel} 已存在，跳过", file=sys.stderr)
        return 0

    # —— chg-03 新增 ——
    # 1) index.md 自动登记
    idx_path = _pad_register_index(root, kind, scope, slug, title)

    # 2) git auto-stage（OQ-5 决策）
    paths_to_stage = [target]
    if idx_path:
        paths_to_stage.append(idx_path)
    git_ok = _pad_git_stage(root, paths_to_stage)

    # 3) 加载链 stderr 活证（复用 _log_project_level_load）
    scope_for_log = {
        "rule": "constraints",
        "experience": "experience",
        "tool": "tools",
    }[kind]
    scope_dir_map = {
        "rule": root / "artifacts" / "project" / "constraints",
        "experience": root / "artifacts" / "project" / "experience" / scope if scope else root / "artifacts" / "project" / "experience",
        "tool": root / "artifacts" / "project" / "tools",
    }
    scope_dir = scope_dir_map[kind]
    hits = sum(1 for f in scope_dir.rglob("*") if f.is_file()) if scope_dir.exists() else 0
    _log_project_level_load(root, scope_for_log, hits, fallback_used=False)

    # 4) stdout 末尾提示 commit
    if git_ok:
        print(f'✓ git staged. 提示 git commit -m "feat: 项目级 {kind}-{title}"')
    else:
        print(f'提示 git add + git commit -m "feat: 项目级 {kind}-{title}"')
    return 0


def _pad_list(root: Path) -> int:
    """req-53 / chg-04：扫 artifacts/project/{constraints,experience/*,tools}/ 6 份 index.md，
    按 kind / scope 分组打印；空段显示 (无)。
    """
    from collections import defaultdict
    base = root / "artifacts" / "project"
    print("=== Project-level Catalog (artifacts/project/) ===\n")

    # rule（constraints/index.md，path 含 {scope}/{slug}.md 子路径）
    print("[rule] (artifacts/project/constraints/)")
    rule_idx = base / "constraints" / "index.md"
    rule_rows = _parse_index_md(rule_idx, source="main") if rule_idx.is_file() else []
    if not rule_rows:
        print("  (无)")
    else:
        # 按 scope 分组
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in rule_rows:
            groups[r.get("scope", "?")].append(r)
        for scope_name in PAD_KINDS["rule"]:
            scope_rows = sorted(groups.get(scope_name, []), key=lambda r: r["path"])
            print(f"  {scope_name}:")
            if not scope_rows:
                print("    (无)")
            for r in scope_rows:
                print(f"    - {r['path']} — {r['title']}")
    print()

    # experience（5 子目录 index.md）
    print("[experience] (artifacts/project/experience/{scope}/)")
    for scope_name in PAD_KINDS["experience"]:
        idx = base / "experience" / scope_name / "index.md"
        rows = _parse_index_md(idx, source="main") if idx.is_file() else []
        rows = sorted(rows, key=lambda r: r["path"])
        print(f"  {scope_name}:")
        if not rows:
            print("    (无)")
        for r in rows:
            print(f"    - {r['path']} — {r['title']}")
    print()

    # tool（tools/index.md「## 项目级工具清单」段，schema 不同）
    print("[tool] (artifacts/project/tools/)")
    tool_idx = base / "tools" / "index.md"
    tool_items = _parse_tool_list_section(tool_idx) if tool_idx.is_file() else []
    if not tool_items:
        print("  (无)")
    for line in sorted(tool_items):
        print(f"  - {line}")
    return 0


def _pad_interactive(root: Path) -> int:
    """req-53 / chg-04：questionary 三步引导（kind → scope → title），完成后调 _pad_add。

    非 TTY 环境直接报错（与 prompt_platform_selection 同款 isatty 守卫）。
    """
    if not sys.stdin.isatty():
        print(
            "[harness pad] ABORT: interactive 模式需要交互式终端；非 TTY 环境请用位置参数。",
            file=sys.stderr,
        )
        return 2
    import questionary as _questionary

    # 步骤 1：选 kind
    kind = _questionary.select(
        "选择类型（kind）:",
        choices=list(PAD_KINDS.keys()),  # ["rule", "experience", "tool"]
        default="rule",
    ).ask()
    if not kind:
        print("[harness pad] cancelled")
        return 1

    # 步骤 2：选 scope（仅 kind=rule/experience 时）
    scope = ""
    if PAD_KINDS[kind]:  # 非空 list 表示需要 scope
        scope = _questionary.select(
            f"选择 {kind} 的 scope:",
            choices=PAD_KINDS[kind],
        ).ask()
        if not scope:
            print("[harness pad] cancelled")
            return 1

    # 步骤 3：输 title
    title = _questionary.text(
        f"{kind}{('/' + scope) if scope else ''} 的标题（≤ 20 字）:",
        validate=lambda v: bool(v.strip()) or "title 不能为空",
    ).ask()
    if not title:
        print("[harness pad] cancelled")
        return 1

    # 调真实 _pad_add
    return _pad_add(root, kind, scope, title.strip())


# ============================================================
# req-49: trivial 通道辅助函数（upstream-fix: 补齐缺失 symbols）
# ============================================================


def get_sequence_for_task_type(task_type: str) -> list[str]:
    """返回给定 task_type 对应的 stage 序列副本。

    req-49 / chg-01: trivial 通道 stage 序列：trivial_define → executing → done。
    支持 req / requirement / bugfix / sug / suggestion / trivial 六种 task_type。
    未知 task_type → ValueError。
    """
    mapping: dict[str, list[str]] = {
        "trivial": TRIVIAL_SEQUENCE,
        "bugfix": BUGFIX_SEQUENCE,
        "req": WORKFLOW_SEQUENCE,
        "requirement": WORKFLOW_SEQUENCE,
        "sug": SUGGESTION_SEQUENCE,
        "suggestion": SUGGESTION_SEQUENCE,
    }
    if task_type not in mapping:
        raise ValueError(f"Unknown task_type: {task_type!r}. Valid: {sorted(mapping)}")
    return list(mapping[task_type])  # return a copy


def validate_stage(task_type: str, stage: str) -> bool:
    """给定 task_type + stage，返回 stage 是否合法（属于对应 sequence）。

    未知 task_type → False（不抛异常）。
    """
    try:
        seq = get_sequence_for_task_type(task_type)
    except ValueError:
        return False
    return stage in seq


def get_next_stage(task_type: str, stage: str) -> str | None:
    """给定 task_type + stage，返回下一个 stage。

    terminal stage 或非法 stage → None。
    """
    try:
        seq = get_sequence_for_task_type(task_type)
    except ValueError:
        return None
    if stage not in seq:
        return None
    idx = seq.index(stage)
    if idx + 1 >= len(seq):
        return None
    return seq[idx + 1]


def is_terminal_stage(task_type: str, stage: str) -> bool:
    """给定 task_type + stage，返回是否为 terminal stage（序列最后一格 = done）。"""
    try:
        seq = get_sequence_for_task_type(task_type)
    except ValueError:
        return False
    return bool(seq) and seq[-1] == stage and stage == seq[-1]


def _next_trivial_id(root: Path) -> str:
    """Return the next available trivial-NN id.

    req-49 / chg-01: trivial task id 分配，扫 state/requirements/ + flow/requirements/。
    """
    max_num = 0
    for d in [
        root / ".workflow" / "state" / "requirements",
        root / ".workflow" / "flow" / "requirements",
    ]:
        if not d.exists():
            continue
        for item in d.iterdir():
            m = re.match(r"trivial-(\d+)", item.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"trivial-{max_num + 1:02d}"


def create_trivial(root: Path, title: str) -> int:
    """req-49 / chg-01: 创建 trivial 任务（几行代码级别改动，走简化流程）。

    产出：
    - .workflow/flow/requirements/{trivial-id}-{slug}/requirement.md（含 task_type: trivial）
    - .workflow/flow/requirements/{trivial-id}-{slug}/trivial-define/trivial-spec.md
    - .workflow/state/requirements/{trivial-id}-{slug}.yaml（task_type=trivial, stage=trivial_define）
    - runtime.yaml 更新（operation_type=trivial, stage=trivial_define）
    """
    config = ensure_config(root)
    runtime = load_requirement_runtime(root)
    trivial_title = title.strip()
    if not trivial_title:
        raise SystemExit("A trivial task title is required.")

    trivial_id = _next_trivial_id(root)
    slug_part = _path_slug(trivial_title)
    dir_name = f"{trivial_id}-{slug_part}" if slug_part else trivial_id
    created: list[str] = []
    skipped: list[str] = []

    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    # requirement.md with task_type: trivial
    req_md_content = (
        f"---\n"
        f"id: {trivial_id}\n"
        f"title: \"{trivial_title}\"\n"
        f"task_type: trivial\n"
        f"stage: trivial_define\n"
        f"status: active\n"
        f"created_at: {date.today().isoformat()}\n"
        f"---\n\n"
        f"# {trivial_id}（{trivial_title}）\n\n"
        f"task_type: trivial — 轻量级通道，仅含 trivial_define / executing / done 三个 stage。\n"
    )
    write_if_missing(flow_req_dir / "requirement.md", req_md_content, created, skipped)

    # trivial-spec.md placeholder
    spec_content = (
        f"# trivial-spec：{trivial_title}\n\n"
        "## 改动描述\n\n- （请在此描述具体改动内容）\n\n"
        "## 完成标准\n\n- （请在此描述完成标准）\n"
    )
    write_if_missing(flow_req_dir / "trivial-define" / "trivial-spec.md", spec_content, created, skipped)

    # state yaml
    state_file = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
    if not state_file.exists():
        today = date.today().isoformat()
        save_simple_yaml(
            state_file,
            {
                "id": trivial_id,
                "title": trivial_title,
                "task_type": "trivial",
                "stage": "trivial_define",
                "status": "active",
                "created_at": today,
                "started_at": today,
                "completed_at": "",
                "stage_timestamps": {},
                "description": "",
            },
            ordered_keys=["id", "title", "task_type", "stage", "status",
                          "created_at", "started_at", "completed_at",
                          "stage_timestamps", "description"],
        )
        created.append(str(state_file.relative_to(root)))

    active_reqs = list(runtime.get("active_requirements", []))
    if trivial_id not in [str(r) for r in active_reqs]:
        active_reqs.append(trivial_id)
    runtime["operation_type"] = "trivial"
    runtime["operation_target"] = trivial_id
    runtime["current_requirement"] = trivial_id
    runtime["current_requirement_title"] = trivial_title
    runtime["stage"] = "trivial_define"
    runtime["active_requirements"] = active_reqs
    save_requirement_runtime(root, runtime)

    print(f"Trivial workspace: {flow_req_dir} [{trivial_title}]")
    for path in created:
        print(f"- created {path}")
    for path in skipped:
        print(f"- skipped {path}")
    return 0


def apply_suggestion_as_trivial(root: Path, sug_id: str) -> int:
    """req-49 / chg-01: 把 sug 池建议作为 trivial 任务执行入口。

    步骤：
    1. 找到 sug 文件（.workflow/flow/suggestions/{sug_id}.md）
    2. 读取 title，调 create_trivial
    3. 把 sug 归档到 archive/
    """
    sug_dir = root / ".workflow" / "flow" / "suggestions"
    sug_file = sug_dir / f"{sug_id}.md"
    if not sug_file.exists():
        raise SystemExit(f"Suggestion not found: {sug_id}")

    # Extract title from frontmatter
    text = sug_file.read_text(encoding="utf-8")
    import re as _re2
    title_match = _re2.search(r"^title:\s*(.+)$", text, _re2.MULTILINE)
    if title_match:
        sug_title = title_match.group(1).strip().strip('"').strip("'")
    else:
        sug_title = sug_id

    # Create trivial task
    rc = create_trivial(root, sug_title)
    if rc != 0:
        return rc

    # Archive the suggestion
    archive_dir = sug_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    sug_file.rename(archive_dir / sug_file.name)

    print(f"Suggestion {sug_id} archived to suggestions/archive/")
    return 0


def classify_diff_change_types(diff: str) -> set[str]:
    """req-49 / chg-02: 根据 git diff 文本分类改动类型。

    返回类型集合，可包含：typo / string / doc / comment / config_constant / other
    空 diff → 返回空集。
    """
    import re as _re3
    if not diff.strip():
        return set()

    types: set[str] = set()
    added_lines: list[str] = []
    removed_lines: list[str] = []
    changed_files: set[str] = set()

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            # extract filename
            m = _re3.search(r"b/(.+)$", line)
            if m:
                changed_files.add(m.group(1))
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(line[1:])

    all_changed = added_lines + removed_lines
    if not all_changed:
        return set()

    # doc: .md / .rst / .txt files
    if any(f.endswith((".md", ".rst", ".txt")) for f in changed_files):
        types.add("doc")

    # config_constant: .yaml / .yml / .json / .toml files
    if any(f.endswith((".yaml", ".yml", ".json", ".toml")) for f in changed_files):
        types.add("config_constant")

    # comment: lines starting with #
    if all(l.strip().startswith("#") for l in all_changed if l.strip()):
        types.add("comment")
        return types

    # Analyze changed lines
    non_comment = [l for l in all_changed if not l.strip().startswith("#")]
    if not non_comment:
        types.add("comment")
        return types

    # Check for complex logic (function definitions, loops, multiple changed lines)
    has_def = any(_re3.match(r"^\s*def ", l) for l in non_comment)
    has_class = any(_re3.match(r"^\s*class ", l) for l in non_comment)
    has_for = any(_re3.match(r"^\s*for ", l) for l in non_comment)
    has_while = any(_re3.match(r"^\s*while ", l) for l in non_comment)
    has_import = any(_re3.match(r"^\s*import |^\s*from .* import", l) for l in non_comment)

    if has_import:
        types.add("other")
        return types

    if has_def or has_class or has_for or has_while or len(non_comment) > 5:
        types.add("other")
        return types

    # Check for string typo fix (single token change in a string)
    if len(added_lines) == 1 and len(removed_lines) == 1:
        a, r = added_lines[0], removed_lines[0]
        if "'" in a or '"' in a:
            types.add("typo")
            types.add("string")
        else:
            types.add("typo")
    else:
        if not types:
            types.add("other")

    return types


def validate_trivial_eligibility(root: Path, *, threshold_lines: int = 10, threshold_files: int = 2) -> tuple[bool, str]:
    """req-49 / chg-02: 校验当前工作区改动是否满足 trivial 通道准入标准。

    Returns (ok: bool, reason: str)。
    ok=True → 满足 trivial 准入；ok=False + reason → 拒绝原因。

    准入条件：
    - git diff (unstaged) 非空
    - 改动文件数 ≤ threshold_files（默认 2）
    - 改动行数（added + removed）≤ threshold_lines（默认 10）
    - 改动类型不含 other（无复杂逻辑 / import 等）
    """
    import subprocess as _sp
    # Get unstaged diff
    result = _sp.run(
        ["git", "diff"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    diff = result.stdout

    if not diff.strip():
        return False, "no diff: 无未暂存的改动，请先修改文件再评估 trivial 准入"

    # Count changed files
    files_result = _sp.run(
        ["git", "diff", "--name-only"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    changed_files = [f for f in files_result.stdout.splitlines() if f.strip()]
    if len(changed_files) > threshold_files:
        return False, f"文件数超标：改动了 {len(changed_files)} 个文件（阈值 {threshold_files}）"

    # Count changed lines
    added = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    total_lines = added + removed
    if total_lines > threshold_lines:
        return False, f"行数超标：改动了 {total_lines} 行（阈值 {threshold_lines}）"

    # Classify change types
    types = classify_diff_change_types(diff)
    if "other" in types:
        return False, "改动类型含 other（复杂逻辑 / import / 函数重构），不适合 trivial 通道"

    return True, "eligible"
