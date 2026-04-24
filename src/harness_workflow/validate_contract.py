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


def run_contract_cli(root: Path, contract: str = "all", regression_dir: Path | None = None) -> int:
    """CLI 入口：``harness validate --contract {all,7,regression,triggers}``。

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

    return 0 if total_violations == 0 else 1
