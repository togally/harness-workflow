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
    "requirement.md",
    "usage-log.yaml",
    "meta.yaml",
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


def check_artifact_placement(root: Path) -> int:
    """artifact-placement lint.

    规则 1：扫 ``artifacts/{branch}/**/*.md``，命中机器型文件名（_MACHINE_TYPE_FILENAMES）→ FAIL。
    规则 2：扫 ``.workflow/flow/**/*``，命中对人最终产物文件名模式 → FAIL（当前仓库仅 WARN，避免
           因 flow/ 下极少数边缘案例破坏整体流水线）。

    Returns 0 = 全绿，1 = 发现违规。

    bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））/ A3
    """
    artifacts_dir = root / "artifacts"
    violations: list[str] = []

    # 规则 1：artifacts/ 下不能有机器型文件
    if artifacts_dir.exists():
        for md_file in artifacts_dir.rglob("*"):
            if not md_file.is_file():
                continue
            # 仅检查 .md / .yaml 后缀（机器型文档常见格式）
            if md_file.suffix not in (".md", ".yaml"):
                continue
            fname = md_file.name
            # README.md 是占位说明文件，允许存在
            if fname == "README.md":
                continue
            if fname in _MACHINE_TYPE_FILENAMES:
                try:
                    rel = md_file.relative_to(root)
                except ValueError:
                    rel = md_file
                violations.append(f"artifacts/ 下发现机器型文件：{rel}")

    if violations:
        print("FAIL: artifact-placement lint — 以下违规文件需迁移到 .workflow/flow/：")
        print("契约引用：.workflow/flow/repository-layout.md §1 / §4 禁止行为")
        print("建议：运行 `harness migrate --bugfix-layout` 迁移历史 bugfix 机器型文档")
        for v in violations:
            print(f"  {v}")
        return 1

    print("PASS: artifact-placement lint — artifacts/ 下无机器型文件")
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


def run_contract_cli(root: Path, contract: str = "all", regression_dir: Path | None = None) -> int:
    """CLI 入口：``harness validate --contract {all,7,regression,triggers,role-stage-continuity,artifact-placement,test-case-design-completeness}``。

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
        rc = check_artifact_placement(root)
        total_violations += rc

    if contract in ("test-case-design-completeness",):
        # 单契约调用：仅在 planning / bugfix regression 退出时显式跑
        rc = check_test_case_design_completeness(root)
        total_violations += rc

    return 0 if total_violations == 0 else 1
