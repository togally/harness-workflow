"""对人文档落盘校验（req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-02（validate_human_docs 重写 + 精简废止项）/ req-41（废四类 brief）/ chg-03（validate_human_docs 重写删四类 brief））。

本模块提供 ``validate_human_docs`` 函数，按 ``.workflow/flow/repository-layout.md``
§2 对人文档白名单，逐条校验 req / bugfix 周期中各 stage 的对人文档是否
真实落盘到 ``artifacts/{branch}/...`` 扁平路径下。

**扫描源（req-id ≥ 41，精简扫描，req-41+）**：
- req 级只扫 ``requirement.md``（raw artifacts 副本）/ ``交付总结.md``。
- 不再要求 ``需求摘要.md`` / ``chg-NN-变更简报.md`` / ``chg-NN-实施说明.md`` /
  ``reg-NN-回归简报.md`` 四类 brief；已存在的空壳 brief 静默忽略。
- ``BRIEF_DEPRECATED_FROM_REQ_ID = 41``：req-id ≥ 此值不扫四类 brief。

**扫描源（req-39 / req-40，现行扫描）**：
- req 级固定扫 ``需求摘要.md`` / ``交付总结.md``；``决策汇总.md`` 可选。
- chg 级扫 req 根目录前缀 ``chg-NN-变更简报.md`` / ``chg-NN-实施说明.md``
  （平铺，不再依赖 ``changes/`` 子目录）。
- reg 级扫 req 根目录前缀 ``reg-NN-回归简报.md``。

**扫描源（req-02 ~ req-38，legacy / mixed 扫描）**：
- 历史存量豁免：req-02 ~ req-37 走 legacy ``changes/`` 子目录扫描；req-38 双轨共存；
  req-39+ 严格新扁平路径。

# req-31（角色功能优化整合与交互精简（合并 sub-stage / 汇报瘦身 / testing-acceptance
# 精简 / 对人文档缩减 / 决策批量化到阶段边界））/ chg-04（S-D 对人文档缩减）废止
# testing / acceptance 两个阶段的对人文档（已从白名单和常量移除，不再扫描）。

**单一真相**：``HUMAN_DOC_CONTRACT`` / ``REQ_LEVEL_DOCS`` / ``CHANGE_LEVEL_DOCS`` /
``BUGFIX_LEVEL_DOCS`` / ``REQ_LEVEL_DOCS_SIMPLIFIED`` 的文件名与
``.workflow/flow/repository-layout.md`` §2 白名单一一对应；修改白名单时必须同步修改本文件。

**不负责**的范围：
- 不校验对人文档的"字段内容完整性"（由各角色自检）。
- 不自动补写缺失文档，只报告。
- regression 级路径（reg-NN-回归简报.md）在 req-39/40 下扫 req 根目录前缀匹配；
  req-41+ 不扫 regression brief（精简扫描）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from harness_workflow.workflow_helpers import (
    FLAT_LAYOUT_FROM_REQ_ID,
    resolve_bugfix_root,
    resolve_requirement_reference,
    resolve_requirement_root,
)


# --- 历史存量豁免常量（溯源 .workflow/flow/repository-layout.md §5）-----------
#
# req-02 ~ req-37：legacy 旧结构（changes/ 子目录），全部保留不迁移。
# req-38：混合过渡期样本，双轨并行（新扁平 chg-NN-变更简报.md 或旧 changes/ 子目录择一命中即 ok）。
# req-39 / req-40：严格新扁平，只扫根目录前缀文件（含四类 brief）。
# req-41+：精简扫描，只扫 raw requirement.md（artifacts 副本）+ 交付总结.md；
#           四类 brief 不再列入白名单（BRIEF_DEPRECATED_FROM_REQ_ID 标记废止边界）。

LEGACY_REQ_ID_CEILING = 37   # req-02 ~ req-37：走 legacy 扫描，废止项已删，不报 missing
MIXED_TRANSITION_REQ_ID = 38  # req-38：双轨共存，新扁平或旧 changes/ 子目录任一命中即 ok

# req-id >= BRIEF_DEPRECATED_FROM_REQ_ID 时，四类 brief（需求摘要 / 变更简报 / 实施说明 / 回归简报）
# 不再列入白名单扫描（req-41（废四类 brief）/ chg-03（validate_human_docs 重写删四类 brief））。
BRIEF_DEPRECATED_FROM_REQ_ID = 41


# --- 契约 3 单一真相映射表（同步 repository-layout.md §2）--------------------
#
# stage → (对人文档文件名, 粒度) 对照 .workflow/flow/repository-layout.md §2 白名单：
#
# req-39 / req-40（现行扫描，四类 brief 仍在白名单）：
#   | requirement_review | 需求摘要.md  | req    |
#   | planning           | 变更简报.md  | chg    |
#   | executing          | 实施说明.md  | chg    |
#   | regression         | 回归简报.md  | reg    |
#   | done               | 交付总结.md  | req    |
#
# req-41+（精简扫描，四类 brief 已从白名单废止）：
#   | raw_artifact       | requirement.md | req  |  （raw artifacts 副本，方便外部审阅）
#   | done               | 交付总结.md    | req  |
#
# 注：testing / acceptance 阶段对人文档已由
# req-31 / chg-04（S-D 对人文档缩减）废止，不在白名单内（常量已移除）。

HUMAN_DOC_CONTRACT: dict[str, tuple[str, str]] = {
    "requirement_review": ("需求摘要.md", "req"),
    "planning": ("变更简报.md", "chg"),
    "executing": ("实施说明.md", "chg"),
    "regression": ("回归简报.md", "reg"),
    "done": ("交付总结.md", "req"),
    # req-41+ 精简扫描新增（四类 brief 废止后的最小集合）
    "raw_artifact": ("requirement.md", "req"),
}

# req 级应产出的对人文档（落在 req 根目录，文件名唯一）
# 适用范围：req-39 / req-40（含四类 brief 的现行扫描）
REQ_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("requirement_review", "需求摘要.md"),
    ("done", "交付总结.md"),
)

# req-41+ 精简扫描：只校验 raw requirement.md（artifacts 副本）+ 交付总结.md
# 四类 brief（需求摘要 / 变更简报 / 实施说明 / 回归简报）不再列入（BRIEF_DEPRECATED_FROM_REQ_ID）
REQ_LEVEL_DOCS_SIMPLIFIED: tuple[tuple[str, str], ...] = (
    ("raw_artifact", "requirement.md"),
    ("done", "交付总结.md"),
)

# change 级应产出的对人文档（chg-NN- 前缀平铺在 req 根目录，或旧 changes/ 子目录）
# 适用范围：req-39 / req-40；req-41+ 不再校验 change 级 brief
CHANGE_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("planning", "变更简报.md"),
    ("executing", "实施说明.md"),
)

# bugfix 级应产出的对人文档（落在 bugfix 根目录）
BUGFIX_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("regression", "回归简报.md"),
    ("executing", "实施说明.md"),
    ("done", "交付总结.md"),
)


STATUS_OK = "ok"
STATUS_MISSING = "missing"
STATUS_MALFORMED = "malformed"


@dataclass
class ValidationItem:
    """单条对人文档校验结果。"""

    stage: str
    filename: str
    expected_path: Path
    status: str  # ok / missing / malformed

    @property
    def icon(self) -> str:
        return {STATUS_OK: "[✓]", STATUS_MISSING: "[ ]", STATUS_MALFORMED: "[!]"}.get(
            self.status, "[?]"
        )


class UnknownTargetError(ValueError):
    """target 格式无法识别或目录不存在时抛出。"""


def _check_doc(path: Path) -> str:
    """判定单个路径的状态：
    - 文件存在且为普通文件 → ok
    - 路径不存在 → missing
    - 路径存在但不是文件（例如被写成目录）→ malformed
    """

    if not path.exists():
        return STATUS_MISSING
    if not path.is_file():
        return STATUS_MALFORMED
    return STATUS_OK


def _extract_req_num(req_dir_name: str) -> int:
    """解析目录名 ``req-NN-slug`` 得到 NN（整数）。

    无法解析时返回 -1（视为 legacy，安全降级）。
    """
    m = re.match(r"req-(\d+)", req_dir_name)
    if m:
        return int(m.group(1))
    return -1


def _collect_chg_items_flat(req_dir: Path) -> list[ValidationItem]:
    """扫 req 根目录下 chg-NN-{变更简报,实施说明}.md 前缀文件（新规扁平路径）。

    返回：找到的 chg 编号集合 × CHANGE_LEVEL_DOCS 的校验条目。
    """
    items: list[ValidationItem] = []
    # 收集 req 根目录下所有 chg-NN- 前缀文件，推断出 chg 编号集合
    chg_nums: set[str] = set()
    for f in req_dir.iterdir():
        if f.is_file():
            m = re.match(r"(chg-\d+)-", f.name)
            if m:
                chg_nums.add(m.group(1))

    for chg_id in sorted(chg_nums):
        for stage, filename in CHANGE_LEVEL_DOCS:
            flat_name = f"{chg_id}-{filename}"
            expected = req_dir / flat_name
            items.append(
                ValidationItem(
                    stage=stage,
                    filename=flat_name,
                    expected_path=expected,
                    status=_check_doc(expected),
                )
            )
    return items


def _collect_chg_items_legacy(req_dir: Path) -> list[ValidationItem]:
    """扫 req/changes/ 子目录（legacy 路径，req-02 ~ req-37）。"""
    items: list[ValidationItem] = []
    changes_dir = req_dir / "changes"
    change_dirs: Iterable[Path] = ()
    if changes_dir.exists() and changes_dir.is_dir():
        change_dirs = sorted(p for p in changes_dir.iterdir() if p.is_dir())

    for change_dir in change_dirs:
        for stage, filename in CHANGE_LEVEL_DOCS:
            expected = change_dir / filename
            items.append(
                ValidationItem(
                    stage=stage,
                    filename=f"{change_dir.name}/{filename}",
                    expected_path=expected,
                    status=_check_doc(expected),
                )
            )
    return items


def _collect_chg_items_mixed(req_dir: Path) -> list[ValidationItem]:
    """混合过渡期（req-38）：新扁平或旧 changes/ 子目录任一命中即 ok。"""
    items: list[ValidationItem] = []

    # 收集所有 chg 编号（新扁平 + 旧 changes/ 子目录）
    chg_nums: set[str] = set()
    for f in req_dir.iterdir():
        if f.is_file():
            m = re.match(r"(chg-\d+)-", f.name)
            if m:
                chg_nums.add(m.group(1))
    changes_dir = req_dir / "changes"
    if changes_dir.exists() and changes_dir.is_dir():
        for p in changes_dir.iterdir():
            if p.is_dir():
                m = re.match(r"(chg-\d+)", p.name)
                if m:
                    chg_nums.add(m.group(1))

    for chg_id in sorted(chg_nums):
        for stage, filename in CHANGE_LEVEL_DOCS:
            flat_path = req_dir / f"{chg_id}-{filename}"
            legacy_change_dir = changes_dir / chg_id if changes_dir.exists() else None

            # 在 changes/ 下可能带 slug，做前缀匹配
            legacy_path: Path | None = None
            if legacy_change_dir is None and changes_dir.exists():
                pass
            if changes_dir.exists() and changes_dir.is_dir():
                for p in changes_dir.iterdir():
                    if p.is_dir() and p.name.startswith(chg_id):
                        legacy_path = p / filename
                        break

            # 任一命中 → ok
            flat_status = _check_doc(flat_path)
            legacy_status = _check_doc(legacy_path) if legacy_path else STATUS_MISSING

            if flat_status == STATUS_OK:
                chosen_path, chosen_status = flat_path, STATUS_OK
            elif legacy_status == STATUS_OK:
                chosen_path, chosen_status = legacy_path, STATUS_OK  # type: ignore[assignment]
            else:
                # 两边都不存在，优先报 flat 路径缺失
                chosen_path, chosen_status = flat_path, STATUS_MISSING

            items.append(
                ValidationItem(
                    stage=stage,
                    filename=f"{chg_id}-{filename}",
                    expected_path=chosen_path,
                    status=chosen_status,
                )
            )
    return items


def _collect_reg_items_flat(req_dir: Path) -> list[ValidationItem]:
    """扫 req 根目录下 reg-NN-回归简报.md 前缀文件（新规扁平路径）。"""
    items: list[ValidationItem] = []
    reg_nums: set[str] = set()
    for f in req_dir.iterdir():
        if f.is_file():
            m = re.match(r"(reg-\d+)-回归简报\.md$", f.name)
            if m:
                reg_nums.add(m.group(1))
    for reg_id in sorted(reg_nums):
        filename = f"{reg_id}-回归简报.md"
        expected = req_dir / filename
        items.append(
            ValidationItem(
                stage="regression",
                filename=filename,
                expected_path=expected,
                status=_check_doc(expected),
            )
        )
    return items


def _collect_req_items_simplified(req_dir: Path) -> list[ValidationItem]:
    """req-41+ 精简扫描：只校验 raw requirement.md（artifacts 副本）+ 交付总结.md。

    四类 brief（需求摘要.md / chg-NN-变更简报.md / chg-NN-实施说明.md / reg-NN-回归简报.md）
    不再列入白名单；已存在的空壳 brief 文件静默忽略（不报期望项也不报额外错）。

    溯源：req-41（废四类 brief）/ chg-03（validate_human_docs 重写删四类 brief）。
    """
    items: list[ValidationItem] = []
    for stage, filename in REQ_LEVEL_DOCS_SIMPLIFIED:
        expected = req_dir / filename
        items.append(
            ValidationItem(
                stage=stage,
                filename=filename,
                expected_path=expected,
                status=_check_doc(expected),
            )
        )
    return items


def _collect_req_items(req_dir: Path) -> list[ValidationItem]:
    """根据 req-id 数字选择扫描路径策略。

    - req-id ≥ BRIEF_DEPRECATED_FROM_REQ_ID (41)：精简扫描，只查 raw requirement.md + 交付总结.md；
      四类 brief 不再校验（废止）。
    - req-id ≤ LEGACY_REQ_ID_CEILING (37)：legacy changes/ 子目录扫描；废止项已从常量删，自然不报 missing。
    - req-id == MIXED_TRANSITION_REQ_ID (38)：双轨共存，新扁平或旧 changes/ 任一命中即 ok。
    - req-id ∈ [39, 40]（FLAT_LAYOUT_FROM_REQ_ID ~ BRIEF_DEPRECATED_FROM_REQ_ID-1）：
      严格新扁平，扫 req 根目录前缀文件（含四类 brief）。
    """
    req_num = _extract_req_num(req_dir.name)

    # req-41+：精简扫描（四类 brief 废止）
    if req_num >= BRIEF_DEPRECATED_FROM_REQ_ID:
        return _collect_req_items_simplified(req_dir)

    items: list[ValidationItem] = []

    # req 级固定文档（req-39/40 现行扫描：需求摘要 + 交付总结，落在 req 根目录）
    for stage, filename in REQ_LEVEL_DOCS:
        expected = req_dir / filename
        items.append(
            ValidationItem(
                stage=stage,
                filename=filename,
                expected_path=expected,
                status=_check_doc(expected),
            )
        )

    if req_num == -1 or req_num <= LEGACY_REQ_ID_CEILING:
        # legacy：changes/ 子目录扫描
        items.extend(_collect_chg_items_legacy(req_dir))
    elif req_num == MIXED_TRANSITION_REQ_ID:
        # 混合过渡期：双轨择一命中即 ok
        items.extend(_collect_chg_items_mixed(req_dir))
    else:
        # 新规（req-39 / req-40）：严格扁平路径（含四类 brief）
        items.extend(_collect_chg_items_flat(req_dir))
        items.extend(_collect_reg_items_flat(req_dir))

    return items


def _collect_bugfix_items(bugfix_dir: Path) -> list[ValidationItem]:
    items: list[ValidationItem] = []
    for stage, filename in BUGFIX_LEVEL_DOCS:
        expected = bugfix_dir / filename
        items.append(
            ValidationItem(
                stage=stage,
                filename=filename,
                expected_path=expected,
                status=_check_doc(expected),
            )
        )
    return items


def _resolve_target(root: Path, target: str) -> tuple[str, Path]:
    """解析 target id 到 (kind, directory)。

    - 以 ``bugfix`` 开头 → 在 ``resolve_bugfix_root`` 下定位
    - 以 ``req`` 开头   → 在 ``resolve_requirement_root`` 下定位
    - 其他 → 同时尝试 req / bugfix

    找不到时抛 UnknownTargetError。
    """

    target = target.strip()
    if not target:
        raise UnknownTargetError("empty target id")

    lowered = target.lower()

    if lowered.startswith("bugfix"):
        bugfix_root = resolve_bugfix_root(root)
        found = resolve_requirement_reference(bugfix_root, target, "cn")
        if found is None:
            raise UnknownTargetError(
                f"bugfix target not found: {target} under {bugfix_root}"
            )
        return "bugfix", found

    if lowered.startswith("req"):
        req_root = resolve_requirement_root(root)
        found = resolve_requirement_reference(req_root, target, "cn")
        if found is None:
            raise UnknownTargetError(
                f"requirement target not found: {target} under {req_root}"
            )
        return "req", found

    # 兜底：尝试 req → bugfix
    req_root = resolve_requirement_root(root)
    found = resolve_requirement_reference(req_root, target, "cn")
    if found is not None:
        return "req", found
    bugfix_root = resolve_bugfix_root(root)
    found = resolve_requirement_reference(bugfix_root, target, "cn")
    if found is not None:
        return "bugfix", found
    raise UnknownTargetError(f"target not found in req/bugfix roots: {target}")


def validate_human_docs(
    root: Path, target: str | None = None
) -> tuple[str, str, list[ValidationItem]]:
    """校验对人文档落盘完整性。

    Args:
        root: 仓库根路径。
        target: 可选的 target id（``req-*`` / ``bugfix-*``）。None 时回退到
            ``runtime.yaml`` 的 ``current_requirement``。

    Returns:
        (kind, target_id, items) 三元组：
          - kind: ``"req"`` / ``"bugfix"``
          - target_id: 解析到的目标 id（目录 basename，包含 slug）
          - items: 每条对人文档的校验结果

    Raises:
        UnknownTargetError: target 无法解析到实际目录。
    """

    if not target:
        # 从 runtime.yaml 读 current_requirement
        from harness_workflow.workflow_helpers import load_requirement_runtime

        runtime = load_requirement_runtime(root)
        target = str(runtime.get("current_requirement", "")).strip()
        if not target:
            raise UnknownTargetError(
                "no target provided and runtime.current_requirement is empty"
            )

    kind, target_dir = _resolve_target(root, target)
    if kind == "req":
        items = _collect_req_items(target_dir)
    else:
        items = _collect_bugfix_items(target_dir)

    return kind, target_dir.name, items


def format_report(kind: str, target_id: str, items: list[ValidationItem], stage: str = "") -> str:
    """渲染人类可读的对人文档清单报告。"""

    header = f"Human Doc Checklist — {target_id} ({kind})"
    if stage:
        header += f" [stage={stage}]"
    lines = [header, "=" * len(header), ""]
    for item in items:
        # 短路径展示：相对 target 的 basename 去掉前缀噪声
        lines.append(f"{item.icon} {item.stage:<20} {item.filename}  →  {item.expected_path}")
    missing = [i for i in items if i.status != STATUS_OK]
    lines.append("")
    if missing:
        lines.append(
            f"Summary: {len(items) - len(missing)}/{len(items)} present, {len(missing)} pending/invalid."
        )
    else:
        lines.append(f"Summary: {len(items)}/{len(items)} present. All human docs landed.")
    return "\n".join(lines)


def run_cli(root: Path, target: str | None) -> int:
    """供 CLI 入口调用：返回 exit code，缺失时非零。"""

    try:
        kind, target_id, items = validate_human_docs(root, target)
    except UnknownTargetError as exc:
        print(f"[harness] validate --human-docs error: {exc}")
        return 2

    # stage 来自 runtime（仅展示）
    stage = ""
    try:
        from harness_workflow.workflow_helpers import load_requirement_runtime

        runtime = load_requirement_runtime(root)
        stage = str(runtime.get("stage", "")).strip()
    except Exception:
        stage = ""

    print(format_report(kind, target_id, items, stage=stage))

    has_failure = any(i.status != STATUS_OK for i in items)
    return 1 if has_failure else 0
