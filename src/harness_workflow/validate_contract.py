"""契约自动化校验 runner（req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 2）。

本模块覆盖 `.workflow/context/roles/stage-role.md` 契约 3 / 4 / 6 / 7
的自动化校验，作为 `harness validate --contract ...` 与 `harness status --lint`
的核心 runner。

覆盖的 sug：

- sug-10（regression 阶段《回归简报.md》契约执行补强）：``check_contract_3_4_regression``
- sug-15（stage 角色产出对人文档后当场 `harness validate` 自检）：CLI 入口
- sug-25（`harness status --lint` 自动化契约 7 校验）：``check_contract_7``
- sug-26（辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展）：复用 ``check_contract_7``
- req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/ chg-02（触发门禁 §3.5.2 + harness validate triggers lint）：``check_contract_triggers``
- bugfix-5（同角色跨 stage 自动续跑硬门禁）：``check_role_stage_continuity``

合规样本：req-30（slug 沟通可读性增强：全链路透出 title）归档产出全部通过。
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import yaml as _yaml  # type: ignore[import]
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


__all__ = [
    "ViolationRecord",
    "check_contract_7",
    "check_contract_3_4_regression",
    "check_contract_triggers",
    "check_role_stage_continuity",
    "check_stage_work_completion",
    "check_artifact_placement",
    "check_schema_audit",
    "check_missing_document",
    "collect_lint_paths",
    "run_contract_cli",
]


_ID_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?P<id>(?:req|chg|sug|bugfix|reg)-\d+)(?![A-Za-z0-9])")

# 对人文档映射：stage → (对人文档名, 粒度)——与 stage-role.md 契约 3 同步。
_REGRESSION_REQUIRED_SECTIONS = ("问题", "根因", "影响", "路由决策")


@dataclass
class ViolationRecord:
    """单条契约 7 违规记录。"""

    file: Path
    line: int
    work_item_id: str
    excerpt: str


def _has_adjacent_title(line: str, start: int, end: int) -> bool:
    """判定 id 首次命中后的"（...）"或 "(...)" 是否紧邻（允许中间 1~3 个 ASCII 空格）。

    规则（req-30（slug 沟通可读性增强：全链路透出 title）契约 7）：
    - 紧邻在 id 之后的全角 `（` 或半角 `(` 括号视为带 title；
    - 允许 0~3 个空格分隔（如 ``req-30 (title)``）；
    - 若整行内已经包含 ``title`` / ``title:`` / ``标题`` 字样（与该 id 关联的 yaml 行等场景），同样视为合规。
    """
    tail = line[end:]
    # 容忍 0~3 个空格后紧跟括号
    stripped = tail.lstrip(" \t")
    if len(tail) - len(stripped) > 3:
        return False
    if stripped.startswith("（") or stripped.startswith("("):
        return True
    # yaml 行：``id: req-99`` + 同行 ``title: ...``——实际场景中较罕见，由本分支兜底
    lowered = line.lower()
    if "title:" in lowered or "title =" in lowered or "title\":" in lowered:
        return True
    return False


def _is_code_fence_boundary(line: str) -> bool:
    """判定行是否为三反引号代码块起讫标记（``` 开头，允许语言标识符）。"""
    stripped = line.strip()
    return stripped.startswith("```")


def _is_indented_code_block(line: str) -> bool:
    """判定行是否为 4 空格缩进代码块行（Markdown 规范）。"""
    return line.startswith("    ") or line.startswith("\t")


def _strip_inline_code_spans(line: str) -> str:
    """将行内 inline 单反引号代码 span（`...`）替换为等长空格，使其内部 id 不参与违规判定。

    req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）：
    - 成对反引号（偶数个）间的内容视为代码 span，替换为空格；
    - 转义反引号（\\`）不视为 span 边界；
    - 奇数个反引号（开放代码 span 未闭合）剩余尾段保留扫描（防止误漏）。
    """
    result = []
    i = 0
    in_span = False
    while i < len(line):
        ch = line[i]
        # 转义反引号（\\`）：整体跳过，不视为 span 边界
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "`":
            if in_span:
                result.append("  ")  # 两个空格替换 \\`
            else:
                result.append(ch)
                result.append(line[i + 1])
            i += 2
            continue
        if ch == "`":
            if not in_span:
                in_span = True
                result.append(" ")  # 替换开头反引号
            else:
                in_span = False
                result.append(" ")  # 替换结尾反引号
        elif in_span:
            result.append(" ")  # 替换 span 内容
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def check_contract_7(root: Path, paths: Iterable[Path]) -> list[ViolationRecord]:
    """扫描给定文件集合，报告契约 7 违规（首次引用裸 id）。

    仅对**每个文件内每个 id 的首次出现**做判定；同一文件同一 id 后续出现不再校验
    （契约 7 允许简写）。

    代码块跳过规则（req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁））：
    - 三反引号代码块（``` ... ```）内的行不参与裸 id 判定；
    - 4 空格 / Tab 缩进代码块行不参与裸 id 判定；
    - inline 单反引号代码 span（`...`）内的 id 不参与裸 id 判定（替换为空格后扫描）。
    """
    violations: list[ViolationRecord] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seen_ids: set[str] = set()
        in_code_fence = False
        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            # 代码块边界检测
            if _is_code_fence_boundary(raw_line):
                in_code_fence = not in_code_fence
                continue  # 起讫行本身也跳过扫描
            # 代码块内或缩进代码块行：跳过
            if in_code_fence or _is_indented_code_block(raw_line):
                continue
            # 剔除 inline 单反引号代码 span 后再扫描
            scan_line = _strip_inline_code_spans(raw_line)
            for m in _ID_PATTERN.finditer(scan_line):
                wid = m.group("id")
                if wid in seen_ids:
                    continue
                seen_ids.add(wid)
                if not _has_adjacent_title(raw_line, m.start(), m.end()):
                    violations.append(
                        ViolationRecord(
                            file=p,
                            line=lineno,
                            work_item_id=wid,
                            excerpt=raw_line.strip()[:160],
                        )
                    )
    return violations


def check_contract_3_4_regression(root: Path, reg_dir: Path) -> list[str]:
    """校验 regression 目录下的《回归简报.md》字段完整性（契约 3 / 4）。

    返回问题描述字符串列表；空列表代表合规。
    """
    issues: list[str] = []
    brief = reg_dir / "回归简报.md"
    if not brief.exists():
        issues.append(f"missing 回归简报.md under {reg_dir}")
        return issues
    text = brief.read_text(encoding="utf-8")
    for section in _REGRESSION_REQUIRED_SECTIONS:
        if f"## {section}" not in text:
            issues.append(f"{brief} missing required section: ## {section}")
    return issues


def collect_lint_paths(root: Path) -> list[Path]:
    """默认扫描范围：
    - ``artifacts/{branch}/**/*.md``
    - ``.workflow/state/sessions/**/session-memory.md``
    - ``.workflow/state/action-log.md``

    归档子目录 ``artifacts/{branch}/archive/`` 默认跳过（见 plan.md 风险 R5）。
    """
    paths: list[Path] = []
    artifacts = root / "artifacts"
    if artifacts.exists():
        for p in artifacts.rglob("*.md"):
            # 跳过归档历史脏数据
            try:
                parts = p.relative_to(artifacts).parts
            except ValueError:
                continue
            if len(parts) >= 2 and parts[1] == "archive":
                continue
            paths.append(p)
    sessions = root / ".workflow/state/sessions"
    if sessions.exists():
        paths.extend(sessions.rglob("session-memory.md"))
    action_log = root / ".workflow/state/action-log.md"
    if action_log.exists():
        paths.append(action_log)
    return paths


def check_contract_triggers(root: Path) -> int:
    """校验 keywords.yaml[api-document-upload].keywords 与 harness-manager.md §3.5.2 镜像列表的一致性。

    req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/ chg-02（触发门禁 §3.5.2 + harness validate triggers lint）

    返回值：
        0 = 两侧一致；1 = 有 diff；
        缺失文件时退出码 0（fallback）+ stderr warn。
    """
    keywords_path = root / ".workflow" / "tools" / "index" / "keywords.yaml"
    harness_manager_path = root / ".workflow" / "context" / "roles" / "harness-manager.md"

    # Fallback：文件缺失时 warn + 退出码 0
    if not keywords_path.exists():
        print(f"skipped: keywords.yaml not found at {keywords_path}", file=sys.stderr)
        return 0
    if not harness_manager_path.exists():
        print(f"skipped: harness-manager.md not found at {harness_manager_path}", file=sys.stderr)
        return 0

    # 读取 keywords.yaml，解析 api-document-upload keywords
    yaml_keywords: set[str] = set()
    if _YAML_AVAILABLE:
        try:
            data = _yaml.safe_load(keywords_path.read_text(encoding="utf-8"))
            for tool in (data or {}).get("tools", []):
                if tool.get("tool_id") == "api-document-upload":
                    kws = tool.get("keywords", [])
                    yaml_keywords = set(kws)
                    break
        except Exception as exc:
            print(f"skipped: failed to parse keywords.yaml: {exc}", file=sys.stderr)
            return 0
    else:
        # yaml 不可用时，用简单正则解析 keywords 行
        text = keywords_path.read_text(encoding="utf-8")
        in_api_section = False
        for line in text.splitlines():
            if "api-document-upload" in line and "tool_id" in line:
                in_api_section = True
            if in_api_section and "keywords:" in line:
                # 提取 ["a", "b", ...] 形态
                m = re.search(r'\[(.+)\]', line)
                if m:
                    raw = m.group(1)
                    yaml_keywords = {
                        kw.strip().strip('"').strip("'")
                        for kw in raw.split(",")
                    }
                break

    # 读取 harness-manager.md §3.5.2 镜像列表
    md_text = harness_manager_path.read_text(encoding="utf-8")
    lines = md_text.splitlines()

    # 定位 §3.5.2 起始行（匹配 "#### 3.5.2" 或 "### 3.5.2"）
    section_start = -1
    section_end = len(lines)
    for i, line in enumerate(lines):
        if re.match(r'^#{2,4}\s+3\.5\.2\s', line):
            section_start = i
        elif section_start >= 0 and i > section_start and re.match(r'^#{2,4}\s+', line):
            section_end = i
            break

    if section_start < 0:
        print("skipped: §3.5.2 section not found in harness-manager.md", file=sys.stderr)
        return 0

    # 提取 §3.5.2 段内"镜像自 keywords.yaml"注释块后紧跟的连续 bullet 列表。
    # 策略：找到 "<!-- 镜像自" 注释行后，收集紧跟的所有 "^- " 行；
    #       遇到空行或非 bullet 行即停止，避免把"硬门禁违反判定"等后续段的列表误收。
    md_keywords: set[str] = set()
    mirror_comment_found = False
    collecting = False
    for line in lines[section_start:section_end]:
        stripped = line.strip()
        if not mirror_comment_found:
            # 找到镜像注释标记行
            if "镜像自" in stripped and stripped.startswith("<!--"):
                mirror_comment_found = True
                collecting = True
            continue
        if collecting:
            bullet_m = re.match(r'^- (.+)$', line)
            if bullet_m:
                md_keywords.add(bullet_m.group(1).strip())
            else:
                # 空行或非 bullet 行 → 镜像块结束
                collecting = False

    # 计算对称差
    only_in_yaml = yaml_keywords - md_keywords
    only_in_md = md_keywords - yaml_keywords

    if only_in_yaml or only_in_md:
        print("trigger keyword drift detected", file=sys.stderr)
        if only_in_yaml:
            print(f"  only in keywords.yaml: {only_in_yaml}", file=sys.stderr)
        if only_in_md:
            print(f"  only in harness-manager.md §3.5.2: {only_in_md}", file=sys.stderr)
        return 1

    return 0


def check_role_stage_continuity(root: Path, text_override: str | None = None) -> int:
    """话术 lint：检测 session-memory.md 是否包含向用户暴露无用户决策点 stage 转换的违规话术。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）：
    契约（stage-role.md:39 / technical-director.md:165 / harness-manager.md:342）规定：
    同一角色覆盖的相邻 stage 之间，或 exit_decision 为 auto/verdict 的 stage 出口，
    默认静默自动连跑，不向用户暴露"是否进 {下一 stage}"决策点。

    修复点 6 扩展规则：
    1. 读 runtime.yaml 取 current_stage；
    2. 扫描近期 session-memory.md + action-log.md（若 text_override 给定则扫 override）；
    3. 正则匹配"是否进(入|到)? {stage_name}"话术，忽略 <!-- lint:ignore role-stage-continuity --> 豁免行；
    4. 命中的 target_stage 与 current_stage 同角色 → FAIL (exit 1)；
    5. current_stage 的 exit_decision in {auto, verdict, terminal} → 任何"是否进 {下一 stage}"都 FAIL；
    6. 命中但 exit_decision 为 explicit/user 且跨角色边界 → PASS（合规决策点，正确行为）。

    Returns:
        0 = PASS；1 = FAIL（有违规话术）。
    """
    try:
        from harness_workflow.workflow_helpers import (
            _load_role_stage_map, _get_role_for_stage,
            _load_stage_policies, _get_exit_decision,
        )
    except ImportError:
        print("skipped: workflow_helpers not importable", file=sys.stderr)
        return 0

    # 读 runtime.yaml 取 current_stage
    runtime_path = root / ".workflow" / "state" / "runtime.yaml"
    current_stage: str = ""
    if runtime_path.exists() and _YAML_AVAILABLE:
        try:
            rt = _yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
            current_stage = str(rt.get("stage", "")).strip()
        except Exception:
            pass

    role_stage_map = _load_role_stage_map(root)
    stage_policies = _load_stage_policies(root)
    current_role = _get_role_for_stage(current_stage, role_stage_map) if current_stage else None
    current_exit = _get_exit_decision(current_stage, stage_policies) if current_stage else "user"

    # 收集 lint 目标文本
    lint_texts: list[tuple[Path, str]] = []
    if text_override is not None:
        lint_texts.append((Path("<mock>"), text_override))
    else:
        # 近期 session-memory.md：扫所有 flow/requirements + flow/bugfixes 下的 session-memory.md
        for sm in list((root / ".workflow" / "flow").rglob("session-memory.md")) if (root / ".workflow" / "flow").exists() else []:
            try:
                lint_texts.append((sm, sm.read_text(encoding="utf-8")))
            except OSError:
                pass
        # artifacts 下的 session-memory.md
        for sm in list((root / "artifacts").rglob("session-memory.md")) if (root / "artifacts").exists() else []:
            try:
                lint_texts.append((sm, sm.read_text(encoding="utf-8")))
            except OSError:
                pass
        # action-log.md
        action_log = root / ".workflow" / "state" / "action-log.md"
        if action_log.exists():
            try:
                lint_texts.append((action_log, action_log.read_text(encoding="utf-8")))
            except OSError:
                pass

    # 正则：匹配中文"是否进入 / 是否进到 / 是否进 {stage}"——只匹配中文形式避免误伤英文产出
    _STAGE_NAMES = [
        "requirement_review", "planning", "ready_for_execution",
        "executing", "testing", "acceptance", "done",
        "regression", "suggestion", "apply",
    ]
    stage_pat = "|".join(re.escape(s) for s in _STAGE_NAMES)
    _LINT_RE = re.compile(
        r"是否进(入|到)?\s*(" + stage_pat + r")",
        re.IGNORECASE,
    )
    _IGNORE_TAG = "<!-- lint:ignore role-stage-continuity -->"
    # 触发全 stage FAIL 的出口决策类型（修复点 6 扩展）
    _AUTO_EXIT_DECISIONS = {"auto", "verdict", "terminal"}

    violations: list[tuple[Path, int, str, str]] = []  # (file, lineno, target_stage, line_text)

    for file_path, text in lint_texts:
        for lineno, line in enumerate(text.splitlines(), start=1):
            # 豁免行（原文引用等）
            if _IGNORE_TAG in line:
                continue
            for m in _LINT_RE.finditer(line):
                target_stage = m.group(2).strip()
                target_role = _get_role_for_stage(target_stage, role_stage_map)
                # 判定是否违规（修复点 6 扩展：两条路径均可触发 FAIL）
                # 路径 A：同角色场景（修复点 2 原逻辑）
                same_role_fail = current_role is not None and target_role == current_role
                # 路径 B：当前 stage 出口为 auto/verdict/terminal，任何"是否进 X"都违规（修复点 6）
                auto_exit_fail = current_exit in _AUTO_EXIT_DECISIONS
                if same_role_fail or auto_exit_fail:
                    violations.append((file_path, lineno, target_stage, line.strip()))

    if violations:
        print(
            "FAIL: role-stage-continuity lint — 以下话术向用户暴露无用户决策点的 stage 转换，违反契约。\n"
            "契约引用：stage-role.md:39 / technical-director.md:165 / harness-manager.md:342\n"
            "建议：角色 X 自动跨 stage 或由 verdict 驱动路由，无需用户决策；请移除或改为自动推进。",
        )
        for fp, ln, ts, excerpt in violations:
            try:
                rel = fp.relative_to(root)
            except ValueError:
                rel = fp
            print(f"  {rel}:{ln}: target_stage={ts} — {excerpt[:120]}")
        return 1

    if current_role is not None:
        print(f"PASS: role-stage-continuity (current_stage={current_stage}, current_role={current_role}, exit_decision={current_exit})")
    else:
        print(f"PASS: role-stage-continuity (current_stage={current_stage or '(none)'}, no role mapping — skip)")
    return 0


# ---------------------------------------------------------------------------
# bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ A3：
# artifact-placement lint：扫 artifacts/ 下机器型文件 + flow/ 下对人文件
# ---------------------------------------------------------------------------

#: 机器型文件名清单（这些文件名不应出现在 artifacts/ 下）
#: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-01（机器型工件路径修复 + 防再犯 lint）
#: 扩展：加入 sug-audit.md / roadmap.md；同时从严格命中中移除 requirement.md（由白名单豁免处理）。
_MACHINE_TYPE_FILENAMES = frozenset({
    "bugfix.md",
    "change.md",
    "plan.md",
    "diagnosis.md",
    "session-memory.md",
    "test-evidence.md",
    "required-inputs.md",
    "analysis.md",
    "decision.md",
    "regression.md",
    "done-report.md",
    "checklist.md",
    "test-report.md",
    "acceptance-report.md",
    "testing-report.md",
    "usage-log.yaml",
    "meta.yaml",
    # req-46 / chg-01 扩展：工作产出类机器型文件名
    "sug-audit.md",
    "roadmap.md",
})

#: requirement.md 白名单豁免路径模式：
#: artifacts/main/requirements/{req-id}-{slug}/requirement.md 是 §2 白名单合法 raw 副本，不应命中 FAIL。
#: 路径模式：artifacts/*/requirements/*/requirement.md（一层 req 目录下直接放置，无 stage-name 子目录）
_REQUIREMENT_MD_WHITELIST_PATTERN = re.compile(
    r"^artifacts/[^/]+/requirements/[^/]+/requirement\.md$"
)

#: stage-name 子目录白名单（这些子目录名出现在 artifacts/main/requirements/{req-id}/ 下时触发 FAIL）
#: req-46 / chg-01 新增规则 0：路径模式扫
_STAGE_NAME_SUBDIRS = frozenset({
    "requirement-review",
    "planning",
    "executing",
    "testing",
    "acceptance",
    "done",
    "regression",
    "regressions",
})

#: 对人最终产物文件名模式（这些文件名不应出现在 .workflow/flow/ 下）
_HUMAN_FACING_PATTERNS = (
    "交付总结.md",
    "决策汇总.md",
    "部署文档",
    "接入配置说明",
    "runbook-",
    "manual-",
    "guide-",
    "contract-",
    ".sql",
    ".pdf",
)


def check_artifact_placement(root: Path, verbose: bool = True) -> int:
    """artifact-placement lint.

    规则 0（新，req-46 / chg-01）：扫 ``artifacts/main/requirements/{req-id}-{slug}/`` 下
           任何 stage-name 子目录（_STAGE_NAME_SUBDIRS）→ FAIL 并报路径。

    规则 1：扫 ``artifacts/{branch}/**/*.md``，命中机器型文件名（_MACHINE_TYPE_FILENAMES）→ FAIL；
           豁免：路径符合 _REQUIREMENT_MD_WHITELIST_PATTERN（§2 白名单 raw 副本）的 requirement.md
           不命中 FAIL（req-46 / chg-01 修复误命中）。

    规则 2：扫 ``.workflow/flow/**/*``，命中对人最终产物文件名模式 → FAIL（当前仓库仅 WARN，避免
           因 flow/ 下极少数边缘案例破坏整体流水线）。

    Args:
        root: 项目根目录
        verbose: True = 打印 PASS/FAIL 详情；False = 静默（仅 harness next 内部 gate）

    Returns 0 = 全绿，64 = 发现违规（via raise_harness_block）。

    bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ A3
    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-01（机器型工件路径修复 + 防再犯 lint）升级
    bugfix-10（req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block）/ 修复
    """
    artifacts_dir = root / "artifacts"
    violations: list[str] = []

    # 历史存量豁免目录（repository-layout.md §4）：下列目录中的遗留结构不触发 lint。
    # - artifacts/{branch}/archive/：legacy 历史归档（req-02 ~ req-40 历史脏数据）
    # - artifacts/{branch}/regressions/：pre-flow-layout 时代的 reg 目录（req-02~req-40 遗留）
    # req-41+ 按本规则严格执行（artifact-placement lint 只扫 req-41+ 活跃目录）。
    _ARCHIVE_EXEMPTION_DIRS = {
        str(artifacts_dir / "main" / "archive"),
        str(artifacts_dir / "main" / "regressions"),
    }

    def _is_under_archive(path: Path) -> bool:
        path_str = str(path)
        return any(path_str.startswith(d) for d in _ARCHIVE_EXEMPTION_DIRS)

    # 规则 0（req-46 / chg-01 新增）：artifacts/main/requirements/{req-id}-{slug}/ 下不能有 stage-name 子目录
    # 注：仅扫 artifacts/main/requirements/（非 archive），豁免历史遗留
    if artifacts_dir.exists():
        req_base = artifacts_dir / "main" / "requirements"
        if req_base.is_dir():
            for req_dir in req_base.iterdir():
                if not req_dir.is_dir():
                    continue
                if _is_under_archive(req_dir):
                    continue  # 历史豁免
                for child in req_dir.iterdir():
                    if child.is_dir() and child.name in _STAGE_NAME_SUBDIRS:
                        try:
                            rel = child.relative_to(root)
                        except ValueError:
                            rel = child
                        violations.append(
                            f"artifacts/ 下发现 stage-name 子目录（机器型工件禁落此处）：{rel}/"
                        )

    # 规则 1：artifacts/ 下不能有机器型文件
    if artifacts_dir.exists():
        for md_file in artifacts_dir.rglob("*"):
            if not md_file.is_file():
                continue
            if _is_under_archive(md_file):
                continue  # 历史存量豁免（repository-layout.md §4）
            # 仅检查 .md / .yaml 后缀（机器型文档常见格式）
            if md_file.suffix not in (".md", ".yaml"):
                continue
            fname = md_file.name
            # README.md 是占位说明文件，允许存在
            if fname == "README.md":
                continue
            # requirement.md 白名单豁免：artifacts/*/requirements/*/requirement.md 是 §2 合法 raw 副本
            # 路径级别要求：直接在 req-slug 目录下（无 stage-name 子目录层），才豁免
            if fname == "requirement.md":
                try:
                    rel_str = str(md_file.relative_to(root))
                except ValueError:
                    rel_str = str(md_file)
                if _REQUIREMENT_MD_WHITELIST_PATTERN.match(rel_str):
                    continue  # 白名单豁免，跳过
                # 不在白名单位（如在 stage-name 子目录下）仍命中 FAIL
            if fname in _MACHINE_TYPE_FILENAMES:
                try:
                    rel = md_file.relative_to(root)
                except ValueError:
                    rel = md_file
                violations.append(f"artifacts/ 下发现机器型文件：{rel}")

    if violations:
        detail = (
            f"{len(violations)} violations — 机器型文件落 artifacts/ 区，应在 .workflow/flow/\n"
            + "\n".join(f"  {v}" for v in violations)
        )
        if verbose:
            print("FAIL: artifact-placement lint — 以下违规文件需迁移到 .workflow/flow/：")
            print("契约引用：.workflow/flow/repository-layout.md §1 / §3 / §4 禁止行为")
            for v in violations:
                print(f"  {v}")
        try:
            from harness_workflow.workflow_helpers import raise_harness_block
            return raise_harness_block(
                error_type="artifact-placement",
                fix_checklist_path=".workflow/context/checklists/fix-artifact-placement.md",
                retry_context={"violations": violations[:5]},
                severity="FAIL",
                detected_by="executing",
                root=root,
            )
        except ImportError:
            return 1

    if verbose:
        print("PASS: artifact-placement lint — artifacts/ 下无机器型文件")
    return 0


# ---------------------------------------------------------------------------
# req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
# / chg-02（fix-checklist 首批 3 个 + lint 输出加指针）
# bugfix-10（req-48 chg-02 实施缺陷：3 个 contract 未真正接入 raise_harness_block）/ 修复
# check_schema_audit：扫 .workflow/state/requirements/ 下旧格式目录（无 slug）→ HARNESS_BLOCK
# ---------------------------------------------------------------------------


def check_schema_audit(root: Path, verbose: bool = True) -> int:
    """schema-audit lint：扫 .workflow/state/requirements/ 下旧格式目录（无 slug，仅 req-NN）→ HARNESS_BLOCK。

    规则：``state/requirements/req-{N}``（纯数字，无 slug 后缀）是 pre-req-30 遗留格式，应归档或重命名。
    符合格式的 yaml 文件（req-NN-slug.yaml）和 archive/ 子目录豁免。

    Args:
        root: 项目根目录
        verbose: True = 打印详情；False = 静默

    Returns 0 = 全绿，64 = 发现违规（via raise_harness_block）。
    """
    req_state = root / ".workflow" / "state" / "requirements"
    violations: list[str] = []

    if req_state.is_dir():
        for entry in req_state.iterdir():
            # 豁免：archive/ 子目录
            if entry.name == "archive":
                continue
            # 豁免：正常命名的 yaml 文件（req-NN-slug.yaml）
            if entry.is_file() and entry.suffix in (".yaml", ".yml"):
                continue
            # 检测：目录且名称符合 req-NN（无 slug）模式
            if entry.is_dir() and re.match(r"^req-\d+$", entry.name):
                violations.append(f"旧格式目录（无 slug）：{entry.relative_to(root)}/")

    if violations:
        if verbose:
            print("FAIL: schema-audit lint — 以下旧格式目录需归档或重命名：")
            for v in violations:
                print(f"  {v}")
            print("fix-checklist: .workflow/context/checklists/fix-schema-audit.md")
        try:
            from harness_workflow.workflow_helpers import raise_harness_block
            return raise_harness_block(
                error_type="schema-audit",
                fix_checklist_path=".workflow/context/checklists/fix-schema-audit.md",
                retry_context={"violations": [str(v) for v in violations[:5]]},
                severity="FAIL",
                detected_by="executing",
                root=root,
            )
        except ImportError:
            return 1

    if verbose:
        print("PASS: schema-audit lint — state/requirements/ 下无旧格式目录")
    return 0


# ---------------------------------------------------------------------------
# req-48 / chg-02 + bugfix-10
# check_missing_document：扫 planning 阶段 requirements/{req-id}/ 下 changes/ 为空 → HARNESS_BLOCK
# ---------------------------------------------------------------------------


def check_missing_document(root: Path, verbose: bool = True) -> int:
    """missing-document lint：planning 阶段下 changes/ 为空（无 chg-XX 子目录）→ HARNESS_BLOCK。

    仅在 runtime.yaml stage=planning 时执行；无 runtime.yaml 则直接 PASS（跳过）。
    检测：.workflow/flow/requirements/{req-id-slug}/changes/ 存在但为空（无 chg-XX 子目录）→ FAIL。

    Args:
        root: 项目根目录
        verbose: True = 打印详情；False = 静默

    Returns 0 = 全绿或已跳过，64 = 发现违规（via raise_harness_block）。
    """
    runtime_path = root / ".workflow" / "state" / "runtime.yaml"
    if not runtime_path.exists():
        if verbose:
            print("PASS: missing-document lint — 无 runtime.yaml，跳过检查")
        return 0

    try:
        if _YAML_AVAILABLE:
            runtime_data = _yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
        else:
            # 极简 fallback：按行 key: value 解析
            runtime_data = {}
            for line in runtime_path.read_text(encoding="utf-8").splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    runtime_data[k.strip()] = v.strip().strip('"')
    except Exception:
        if verbose:
            print("PASS: missing-document lint — runtime.yaml 解析失败，跳过检查")
        return 0

    stage = runtime_data.get("stage", "")
    current_req = runtime_data.get("current_requirement", "")

    if stage != "planning" or not current_req:
        if verbose:
            print(f"PASS: missing-document lint — stage={stage!r}，非 planning，跳过检查")
        return 0

    # 扫 .workflow/flow/requirements/ 下匹配 current_req 的目录
    flow_reqs = root / ".workflow" / "flow" / "requirements"
    violations: list[str] = []
    if flow_reqs.is_dir():
        for req_dir in flow_reqs.iterdir():
            if not req_dir.is_dir():
                continue
            # 匹配：目录名以 current_req 开头（req-99 或 req-99-slug）
            if not req_dir.name.startswith(current_req):
                continue
            changes_dir = req_dir / "changes"
            if changes_dir.is_dir():
                # 检查是否有 chg-XX 子目录
                chg_dirs = [c for c in changes_dir.iterdir()
                            if c.is_dir() and c.name.startswith("chg-")]
                if not chg_dirs:
                    violations.append(f"planning 阶段 changes/ 为空：{changes_dir.relative_to(root)}/")

    if violations:
        if verbose:
            print("FAIL: missing-document lint — planning 阶段 changes/ 缺 chg-XX 子目录：")
            for v in violations:
                print(f"  {v}")
            print("fix-checklist: .workflow/context/checklists/fix-missing-document.md")
        try:
            from harness_workflow.workflow_helpers import raise_harness_block
            return raise_harness_block(
                error_type="missing-document",
                fix_checklist_path=".workflow/context/checklists/fix-missing-document.md",
                retry_context={"missing": [str(v) for v in violations[:5]]},
                severity="FAIL",
                detected_by="executing",
                root=root,
            )
        except ImportError:
            return 1

    if verbose:
        print("PASS: missing-document lint — planning 阶段 changes/ 结构完整")
    return 0


# ---------------------------------------------------------------------------
# bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ B5 + C3：
# test-case-design-completeness lint：扫 plan.md + bugfix diagnosis.md 含测试用例设计段
# ---------------------------------------------------------------------------


def check_test_case_design_completeness(root: Path, target_file: Path | None = None) -> int:
    """test-case-design-completeness lint.

    规则 1（plan.md）：plan.md 缺 §测试用例设计 / §4. 测试用例设计 段 → FAIL。
    规则 2（bugfix diagnosis.md）：.workflow/flow/bugfixes/{dir}/regression/diagnosis.md 缺
                                   §测试用例设计 段 → FAIL。
    规则 3（用例数）：§测试用例设计 段内没有任何表格行（用例记录）→ FAIL（用例数=0 视为违规）。

    如果 target_file 指定，则仅检查该文件；否则全仓库扫描。

    Returns 0 = 全绿，1 = 发现违规。

    bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ B5 + C3
    """
    violations: list[str] = []
    _TEST_DESIGN_MARKERS = (
        "## 4. 测试用例设计",
        "## 4.测试用例设计",
        "## 测试用例设计",
        "## Test Case Design",
        "## 4. Test Case Design",
    )

    def _has_test_design_section(path: Path) -> tuple[bool, bool]:
        """返回 (has_section, has_cases)."""
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return False, False
        has_section = any(marker in content for marker in _TEST_DESIGN_MARKERS)
        if not has_section:
            return False, False
        # 检查：§测试用例设计 段内是否有表格数据行
        # 数据行定义：以 | 开头、不是全-分隔行（|---|---）、不是表头行（|用例名|...）
        lines_after = False
        in_section = False
        for line in content.splitlines():
            if any(marker in line for marker in _TEST_DESIGN_MARKERS):
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break  # 进入下一 section
            if in_section and line.strip().startswith("|") and "|" in line[1:]:
                stripped = line.strip()
                # 跳过纯分隔行（由 |---| 构成，允许 : 对齐符）
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if all(re.match(r"^[-:]+$", c) for c in cells if c):
                    continue  # 分隔行
                # 跳过表头行（含 "用例名" 或 "Test Case"）
                if "用例名" in stripped or "Test Case" in stripped:
                    continue
                # 其他非空 | 行 = 数据行
                if any(c.strip() for c in cells):
                    lines_after = True
                    break
        return has_section, lines_after

    files_to_check: list[tuple[Path, str]] = []

    if target_file is not None:
        files_to_check.append((target_file, "指定文件"))
    else:
        # 扫描 plan.md 文件（flow layout）
        flow_reqs = root / ".workflow" / "flow" / "requirements"
        if flow_reqs.exists():
            for plan_file in flow_reqs.rglob("plan.md"):
                files_to_check.append((plan_file, "plan.md"))

        # 扫描 bugfix diagnosis.md 文件（flow layout）
        flow_bugfixes = root / ".workflow" / "flow" / "bugfixes"
        if flow_bugfixes.exists():
            for diag_file in flow_bugfixes.rglob("diagnosis.md"):
                files_to_check.append((diag_file, "bugfix diagnosis.md"))

    for fpath, ftype in files_to_check:
        if not fpath.exists():
            continue
        has_section, has_cases = _has_test_design_section(fpath)
        try:
            rel = fpath.relative_to(root)
        except ValueError:
            rel = fpath
        if not has_section:
            violations.append(f"{ftype} 缺 §测试用例设计 章节：{rel}")
        elif not has_cases:
            violations.append(f"{ftype} §测试用例设计 章节内用例数=0（未填写具体用例）：{rel}")

    if violations:
        print("FAIL: test-case-design-completeness lint — 以下文件缺 §测试用例设计 或用例数=0：")
        print("契约引用：analyst.md Step B2.5 / regression.md Step 4.5 / evaluation/testing.md §0")
        for v in violations:
            print(f"  {v}")
        return 1

    if files_to_check:
        print(f"PASS: test-case-design-completeness lint — 已检查 {len(files_to_check)} 个文件，全部含 §测试用例设计 且有用例")
    else:
        print("PASS: test-case-design-completeness lint — 无 plan.md / bugfix diagnosis.md 可扫描")
    return 0


def check_stage_work_completion(root: Path) -> int:
    """校验当前 stage 关键产物是否齐全。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    对应 AC-05（lint 子命令）。

    读取 runtime.yaml 取 stage + operation_type + current_requirement，
    调用 _is_stage_work_done 判断；缺项时 stdout 列具体文件路径。

    Returns:
        0 = PASS（产物齐全）；1 = FAIL（缺产物）。
    """
    try:
        from harness_workflow.workflow_helpers import _is_stage_work_done
    except ImportError:
        print("skipped: workflow_helpers not importable", file=sys.stderr)
        return 0

    runtime_path = root / ".workflow" / "state" / "runtime.yaml"
    if not runtime_path.exists():
        print("skipped: runtime.yaml not found", file=sys.stderr)
        return 0

    rt: dict = {}
    if _YAML_AVAILABLE:
        try:
            rt = _yaml.safe_load(runtime_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"skipped: failed to parse runtime.yaml: {e}", file=sys.stderr)
            return 0
    else:
        print("skipped: pyyaml not available", file=sys.stderr)
        return 0

    stage = str(rt.get("stage", "")).strip()
    operation_type = str(rt.get("operation_type", "requirement")).strip()
    req_id = str(rt.get("current_requirement", "")).strip()

    if not stage or not req_id:
        print("skipped: stage or current_requirement missing from runtime.yaml", file=sys.stderr)
        return 0

    done = _is_stage_work_done(stage, root, req_id, operation_type)
    if done:
        print(f"PASS: stage-work-completion ({stage} 产物齐全)")
        return 0

    # FAIL：列具体缺项
    print(f"FAIL: stage-work-completion — stage={stage} 产物不完整，请补全以下文件：")
    if operation_type == "bugfix":
        flow_base = root / ".workflow" / "flow" / "bugfixes"
    else:
        flow_base = root / ".workflow" / "flow" / "requirements"

    # 找 flow 目录
    req_flow: "Path | None" = None
    if flow_base.exists():
        matches = [d for d in flow_base.iterdir() if d.is_dir() and (d.name.startswith(f"{req_id}-") or d.name == req_id)]
        if matches:
            req_flow = matches[0]

    if stage == "testing":
        report_path = (req_flow / "test-report.md") if req_flow else None
        if report_path is None or not report_path.exists():
            print(f"  缺失：{report_path or f'.workflow/flow/.../{req_id}-*/test-report.md'}")
        else:
            print(f"  存在但缺 §结论 段：{report_path}")
    elif stage == "acceptance":
        checklist_path = (req_flow / "acceptance" / "checklist.md") if req_flow else None
        if checklist_path is None or not checklist_path.exists():
            print(f"  缺失：{checklist_path or f'.workflow/flow/.../{req_id}-*/acceptance/checklist.md'}")
        else:
            print(f"  存在但缺 §结论 段：{checklist_path}")
    else:
        print(f"  stage={stage} 产物未齐（详见 chg-01 plan.md §1 产物规则）")

    # 确保输出含 "test-report.md" 关键字用于 TC-07 断言
    if stage == "testing":
        pass  # 已在上方 print
    return 1


def check_testing_no_destructive_git(root: Path, req_id: str | None = None) -> int:
    """testing-no-destructive-git lint.

    扫描 testing subagent action-log.md 是否含破坏性 git 命令。

    默认扫描范围：所有 req-id ≥ 41 活跃目录的 action-log.md。
    指定 req_id 时仅扫该 req。

    破坏性命令 regex：
        \\bgit\\s+(restore|reset\\s+--hard|checkout\\s+\\.|clean\\s+-f|branch\\s+-D|rebase\\s+-i)\\b
        （不含 --dry-run / --no-commit -n / 读操作等白名单豁免形态）

    WARN 模式（默认）：exit 0 + stderr 报告命中行。
    后续 chg 可切换为 FAIL 模式（exit 1），本 chg 不强切。

    Returns:
        0 = PASS（无命中，WARN 模式下命中也返回 0）。

    req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
    chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地 sug-51（testing git restore 事故 + tmpdir 红线）。
    """
    # 破坏性 git 命令 regex（不含白名单形态）
    _DESTRUCTIVE_RE = re.compile(
        r"\bgit\s+(?:restore|reset\s+--hard|checkout\s+\.|clean\s+-f|branch\s+-D|rebase\s+-i)\b"
    )
    # 白名单豁免：含这些 flag 的行不视为破坏性
    _WHITELIST_PATTERNS = (
        "--dry-run",
        "--no-commit -n",
        "--no-commit",
        "git diff",
        "git log",
        "git show",
        "git revert --no-commit",
    )

    sessions_dir = root / ".workflow" / "state" / "sessions"
    if not sessions_dir.exists():
        print("PASS: testing-no-destructive-git (no sessions dir found)", file=sys.stderr)
        return 0

    warn_records: list[tuple[Path, int, str]] = []  # (file, lineno, excerpt)

    def _should_scan_req(dir_name: str) -> bool:
        """仅扫 req-id ≥ 41 目录（形如 req-41 / req-42 等）。"""
        m = re.match(r"^req-(\d+)$", dir_name)
        if m:
            return int(m.group(1)) >= 41
        return False

    scan_dirs: list[Path] = []
    if req_id:
        target_dir = sessions_dir / req_id
        if target_dir.exists():
            scan_dirs.append(target_dir)
        # 也扫 sessions_dir 下含 req_id 前缀的目录
        for d in sessions_dir.iterdir():
            if d.is_dir() and d.name == req_id and d not in scan_dirs:
                scan_dirs.append(d)
    else:
        for d in sessions_dir.iterdir():
            if d.is_dir() and _should_scan_req(d.name):
                scan_dirs.append(d)

    for req_dir in scan_dirs:
        action_log = req_dir / "action-log.md"
        if not action_log.exists():
            continue
        try:
            lines = action_log.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, start=1):
            # 白名单豁免：含白名单 pattern 的行跳过
            if any(wp in line for wp in _WHITELIST_PATTERNS):
                continue
            if _DESTRUCTIVE_RE.search(line):
                warn_records.append((action_log, lineno, line.strip()[:120]))

    if warn_records:
        print(
            f"WARN: testing-no-destructive-git — 发现 {len(warn_records)} 行破坏性 git 命令（WARN 模式，exit 0）",
            file=sys.stderr,
        )
        print(
            "  溯源：sug-51（testing git restore 事故 + tmpdir 红线）/ testing.md §破坏性 git 命令禁止",
            file=sys.stderr,
        )
        for fpath, ln, excerpt in warn_records:
            try:
                rel = fpath.relative_to(root)
            except ValueError:
                rel = fpath
            print(f"  {rel}:{ln}: {excerpt}", file=sys.stderr)
        return 0  # WARN 模式：默认 exit 0，后续 chg 可切 FAIL

    print("PASS: testing-no-destructive-git (no destructive git commands found)")
    return 0


# --------------------------------------------------------------------------- #
# bugfix-8 / chg-04：user-write-protected-zones 硬门禁 + dev-mode 三层探测      #
# --------------------------------------------------------------------------- #

def _is_dev_repo(root: Path) -> bool:
    """三层探测本仓 / 用户项目分离边界。"""
    import re as _re
    import os
    # 1) pyproject.toml::name == "harness-workflow"
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            m = _re.search(r'name\s*=\s*["\']harness-workflow["\']', content)
            if m:
                return True
        except Exception:
            pass
    # 2) src/harness_workflow/ 源码目录存在
    if (root / "src" / "harness_workflow").exists():
        return True
    # 3) HARNESS_DEV_REPO_ROOT env 命中
    dev_env = os.environ.get("HARNESS_DEV_REPO_ROOT")
    if dev_env:
        try:
            if Path(dev_env).resolve() == root.resolve():
                return True
        except Exception:
            pass
    return False


def check_user_write_protected_zones(root: Path) -> int:
    """硬门禁：用户项目模式下扫描 .workflow/ + skill/commands 目录，识别野文件。

    返回：违规文件数（0 = PASS / >0 = ABORT）。
    """
    # 1) dev mode 自动豁免
    if _is_dev_repo(root):
        return 0

    # 2) 用户项目模式：扫保护区
    from harness_workflow.workflow_helpers import (
        _scaffold_v2_file_contents,
        _load_managed_state,
        _SCAFFOLD_V2_MIRROR_WHITELIST,
    )

    # bugfix-9 / chg-02（skill/commands 目录移出扫描列表修复误报）：
    # .{claude,codex,kimi,qoder}/skills/ 与 .{claude,codex,kimi,qoder}/commands/ 是
    # install_local_skills() 的纯工具产出目录，不可能有用户自定义文件（install 时会全量覆盖）。
    # 误入保护列表导致 PetMall 等项目每次 install 后产生 269 个误报 violation。
    # 简单方案：直接将这些目录从 protected_zones 中移除，只保留 .workflow/。
    # 保护语义无损：工具产出目录内若有"野文件"，install 时会被覆盖或反向清理消除。
    protected_zones = [
        ".workflow",
    ]

    mirror = _scaffold_v2_file_contents(root, include_agents=False, include_claude=False, language="cn")
    managed = _load_managed_state(root)

    violations: list[str] = []
    for zone in protected_zones:
        zone_path = root / zone
        if not zone_path.exists():
            continue
        for f in zone_path.rglob("*"):
            if not f.is_file():
                continue
            relative = f.relative_to(root).as_posix()
            # 三级豁免
            if relative in mirror:
                continue
            if relative in managed:
                continue
            if any(w in relative for w in _SCAFFOLD_V2_MIRROR_WHITELIST):
                continue
            violations.append(relative)

    if violations:
        print(
            f"\033[31m[user-write-protected-zones] ABORT: {len(violations)} violation(s) — 用户野文件命中保护区:\033[0m",
            file=sys.stderr,
        )
        for v in violations[:30]:
            print(f"  - {v}", file=sys.stderr)
        if len(violations) > 30:
            print(f"  ... and {len(violations) - 30} more", file=sys.stderr)
        print("Hint: 用户自定义内容请放 artifacts/ 下；保护区仅 harness 工具能写。", file=sys.stderr)
        return len(violations)
    return 0


# --------------------------------------------------------------------------- #
# bugfix-8 / chg-05：build-cache-freshness dev mode lint                       #
# --------------------------------------------------------------------------- #

def check_build_cache_freshness(root: Path) -> int:
    """dev mode lint：扫 build/lib/ 与 src/ 的差集，发现 stale 残留则 WARN（不 ABORT）。"""
    if not _is_dev_repo(root):
        return 0
    build_lib = root / "build" / "lib" / "harness_workflow"
    src_pkg = root / "src" / "harness_workflow"
    if not build_lib.exists() or not src_pkg.exists():
        return 0
    stale = []
    for f in build_lib.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(build_lib)
        src_equiv = src_pkg / rel
        if not src_equiv.exists():
            stale.append(str(rel))
    if stale:
        print(
            f"\033[33m[build-cache-freshness] WARNING: build/lib 含 {len(stale)} 个 src/ 已删的 stale 文件:\033[0m",
            file=sys.stderr,
        )
        for s in stale[:10]:
            print(f"  - {s}", file=sys.stderr)
        if len(stale) > 10:
            print(f"  ... and {len(stale) - 10} more", file=sys.stderr)
        print("Hint: 跑 `rm -rf build/` 清理后再 `pipx install --force`。", file=sys.stderr)
        return len(stale)  # non-zero return signals stale presence (WARN level, not ABORT)
    return 0


# ---------------------------------------------------------------------------
# req-50（现有流程优化）/ chg-05（reviewer 加项 + llm-only-docs contract）：
# _lint_llm_only_docs：扫机器型模板，检测 frontmatter 完整性 + 禁止对人解释段 + 行数上限
# ---------------------------------------------------------------------------

#: LLM-only 文档 lint：禁止出现的"对人解释"段落标题（机器型模板不应含这些标题）
_LLM_ONLY_FORBIDDEN_HEADINGS = (
    "## 背景",
    "## 历史关联",
    "## 用户原话",
    "## 修订说明",
)

#: 机器型模板行数上限（参考 chg-03/chg-04 LLM-only 重写目标：紧凑 markdown，不超 80 行）
_LLM_ONLY_MAX_LINES = 80


def _lint_llm_only_docs(root: Path, verbose: bool = True) -> list[str]:
    """LLM-only 文档 lint：扫机器型模板，检测 frontmatter + 禁止段落 + 行数上限。

    req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）/
    chg-05（reviewer 加项 + llm-only-docs contract）

    扫描路径：
    - src/harness_workflow/assets/skill/assets/templates/（开发仓库）
    - .claude/skills/harness/assets/templates/（也扫 scaffold 同步产物，但仅在 dev 模式）

    判断"机器型"的方式：frontmatter 中含 operation_type 字段（值不为空）。
    如果文件连 frontmatter 都没有（不以 '---' 开头），则跳过（不是机器型模板）。

    规则：
    1. 必须以 '---' YAML frontmatter 开头
    2. frontmatter 中必须含 operation_type 字段（且值非空占位符模式下可含 {{...}}）
    3. 禁止含对人解释段落标题（_LLM_ONLY_FORBIDDEN_HEADINGS）
    4. 行数不超过 _LLM_ONLY_MAX_LINES

    Returns:
        violations: 违规描述字符串列表；空列表 = 全通过。
    """
    violations: list[str] = []

    # 扫描目录：先找 src 路径，再找 .claude 路径（dev 仓中两者都存在）
    scan_dirs: list[Path] = []
    src_templates = root / "src" / "harness_workflow" / "assets" / "skill" / "assets" / "templates"
    if src_templates.exists():
        scan_dirs.append(src_templates)
    else:
        # 用户项目（非 dev）只有 .claude 路径
        claude_templates = root / ".claude" / "skills" / "harness" / "assets" / "templates"
        if claude_templates.exists():
            scan_dirs.append(claude_templates)

    for tmpl_dir in scan_dirs:
        for tmpl_file in sorted(tmpl_dir.glob("*.tmpl")):
            try:
                content = tmpl_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            lines = content.splitlines()

            # 只检查机器型模板（以 '---' frontmatter 开头 + 含 operation_type）
            if not content.startswith("---"):
                continue  # 非 frontmatter 模板：不是机器型，跳过

            # 解析 frontmatter 块（找到第二个 '---' 为止）
            fm_end = -1
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    fm_end = i
                    break
            if fm_end < 0:
                # frontmatter 未闭合 → 视为缺 frontmatter 违规
                violations.append(
                    f"{tmpl_file.name}: frontmatter 未闭合（缺第二个 '---'）"
                )
                continue

            fm_text = "\n".join(lines[1:fm_end])
            if "operation_type" not in fm_text:
                # 有 frontmatter 但无 operation_type → 非机器型，跳过
                continue

            # 规则 3：禁止对人解释段落标题
            for forbidden in _LLM_ONLY_FORBIDDEN_HEADINGS:
                if forbidden in content:
                    violations.append(
                        f"{tmpl_file.name}: 含禁止的对人解释段落「{forbidden}」"
                    )

            # 规则 4：行数上限
            line_count = len(lines)
            if line_count > _LLM_ONLY_MAX_LINES:
                violations.append(
                    f"{tmpl_file.name}: 行数 {line_count} 超过上限 {_LLM_ONLY_MAX_LINES}"
                )

    if verbose and not violations:
        print("PASS: llm-only-docs lint — 所有机器型模板符合 LLM-only 规范")
    elif verbose and violations:
        print(f"FAIL: llm-only-docs lint — 发现 {len(violations)} 个违规：")
        for v in violations:
            print(f"  {v}")

    return violations


def run_contract_cli(root: Path, contract: str = "all", regression_dir: Path | None = None) -> int:
    """CLI 入口：``harness validate --contract {all,7,regression,triggers,role-stage-continuity,artifact-placement,test-case-design-completeness,testing-no-destructive-git,llm-only-docs}``。

    Returns:
        0 = 合规；1 = 发现违规或缺字段；2 = 参数错误。
    """
    contract = (contract or "all").strip().lower()
    total_violations = 0

    if contract in ("all", "7", "contract7"):
        paths = collect_lint_paths(root)
        violations = check_contract_7(root, paths)
        for v in violations:
            try:
                rel = v.file.relative_to(root)
            except ValueError:
                rel = v.file
            print(f"{rel}:{v.line}: contract-7 bare id {v.work_item_id} — {v.excerpt}")
        total_violations += len(violations)

    if contract in ("all", "regression"):
        # 默认扫描 artifacts/{branch}/requirements/*/regressions/* + bugfixes/*/regressions/*
        artifacts = root / "artifacts"
        if artifacts.exists():
            for reg_root in list(artifacts.glob("*/requirements/*/regressions/*")) + \
                            list(artifacts.glob("*/bugfixes/*/regressions/*")):
                if regression_dir is not None and reg_root != regression_dir:
                    continue
                if reg_root.is_dir():
                    issues = check_contract_3_4_regression(root, reg_root)
                    for issue in issues:
                        print(f"contract-3/4 regression: {issue}")
                    total_violations += len(issues)
        if regression_dir is not None and regression_dir.is_dir():
            issues = check_contract_3_4_regression(root, regression_dir)
            for issue in issues:
                print(f"contract-3/4 regression: {issue}")
            total_violations += len(issues)

    if contract in ("all", "triggers"):
        rc = check_contract_triggers(root)
        total_violations += rc

    if contract in ("role-stage-continuity",):
        # 单契约调用：不聚合进 all（避免 all 因现有 session-memory 话术历史噪声 FAIL）
        rc = check_role_stage_continuity(root)
        total_violations += rc

    if contract in ("artifact-placement",):
        # 单契约调用：不聚合进 all（历史 bugfix-1~5 存量违规避免污染整体 all）
        # 直接 return propagate HARNESS_BLOCK exit code（64 / 0）
        return check_artifact_placement(root, verbose=True)

    if contract in ("schema-audit",):
        # req-48 / chg-02 + bugfix-10：旧格式目录检测
        return check_schema_audit(root, verbose=True)

    if contract in ("missing-document",):
        # req-48 / chg-02 + bugfix-10：planning 阶段 changes/ 为空检测
        return check_missing_document(root, verbose=True)

    if contract in ("test-case-design-completeness",):
        # 单契约调用：仅在 planning / bugfix regression 退出时显式跑
        rc = check_test_case_design_completeness(root)
        total_violations += rc

    if contract in ("stage-work-completion",):
        # req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
        # 单契约调用：校验当前 stage 关键产物是否齐全
        rc = check_stage_work_completion(root)
        total_violations += rc

    if contract in ("testing-no-destructive-git",):
        # req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
        # chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地 sug-51（testing git restore 事故 + tmpdir 红线）
        # WARN 模式：exit 0 + stderr 报告命中行（后续 chg 可切 FAIL）
        rc = check_testing_no_destructive_git(root)
        total_violations += rc

    if contract in ("deployment-sync",):
        # req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
        # chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地 sug-55（chg-02 部署同步契约 dev mode flag）
        # HARNESS_DEV_MODE=1 时豁免部署同步检查
        import os
        dev_mode = os.environ.get("HARNESS_DEV_MODE", "").strip().lower()
        if dev_mode in ("1", "true", "yes"):
            print("PASS: deployment-sync (HARNESS_DEV_MODE=1, dev mode — 部署同步检查已豁免)")
        else:
            # prod/ci 模式：严格检查（基础 import 验证）
            try:
                from harness_workflow.workflow_helpers import _is_stage_work_done  # noqa: F401
                print("PASS: deployment-sync (_is_stage_work_done import OK, 严格模式)")
            except ImportError as exc:
                print(f"FAIL: deployment-sync — ImportError: {exc}", file=sys.stderr)
                total_violations += 1

    if contract in ("user-write-protected-zones",):
        # bugfix-8 / chg-04：用户项目保护区硬门禁（dev mode 自动豁免）
        rc = check_user_write_protected_zones(root)
        if rc == 0:
            print("PASS: user-write-protected-zones")
        total_violations += rc

    if contract in ("build-cache-freshness",):
        # bugfix-8 / chg-05：dev mode lint，扫 build/lib/ 与 src/ 差集（WARN only）
        rc = check_build_cache_freshness(root)
        if rc == 0:
            print("PASS: build-cache-freshness")
        total_violations += rc

    if contract in ("llm-only-docs",):
        # req-50（现有流程优化）/ chg-05（reviewer 加项 + llm-only-docs contract）:
        # 扫机器型模板，检测 frontmatter 完整性 + 禁止对人解释段 + 行数上限
        violations = _lint_llm_only_docs(root, verbose=True)
        total_violations += len(violations)

    return 0 if total_violations == 0 else 1
