"""契约自动化校验 runner（req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 2）。

本模块覆盖 `.workflow/context/roles/stage-role.md` 契约 3 / 4 / 6 / 7
的自动化校验，作为 `harness validate --contract ...` 与 `harness status --lint`
的核心 runner。

覆盖的 sug：

- sug-10（regression 阶段《回归简报.md》契约执行补强）：``check_contract_3_4_regression``
- sug-15（stage 角色产出对人文档后当场 `harness validate` 自检）：CLI 入口
- sug-25（`harness status --lint` 自动化契约 7 校验）：``check_contract_7``
- sug-26（辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展）：复用 ``check_contract_7``

合规样本：req-30（slug 沟通可读性增强：全链路透出 title）归档产出全部通过。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


__all__ = [
    "ViolationRecord",
    "check_contract_7",
    "check_contract_3_4_regression",
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


def check_contract_7(root: Path, paths: Iterable[Path]) -> list[ViolationRecord]:
    """扫描给定文件集合，报告契约 7 违规（首次引用裸 id）。

    仅对**每个文件内每个 id 的首次出现**做判定；同一文件同一 id 后续出现不再校验
    （契约 7 允许简写）。
    """
    violations: list[ViolationRecord] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        seen_ids: set[str] = set()
        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            for m in _ID_PATTERN.finditer(raw_line):
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


def run_contract_cli(root: Path, contract: str = "all", regression_dir: Path | None = None) -> int:
    """CLI 入口：``harness validate --contract {all,7,regression}``。

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

    return 0 if total_violations == 0 else 1
