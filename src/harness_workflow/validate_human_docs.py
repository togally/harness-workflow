"""对人文档落盘校验（req-28 / chg-05，AC-09）。

本模块提供 ``validate_human_docs`` 函数，按 ``.workflow/context/roles/stage-role.md``
契约 3 的对人文档映射表，逐条校验 req / bugfix 周期中各 stage 的对人文档是否
真实落盘到 ``artifacts/{branch}/...`` 路径下。

**单一真相**：本文件 ``HUMAN_DOC_CONTRACT`` / ``REQ_LEVEL_DOCS`` /
``CHANGE_LEVEL_DOCS`` / ``BUGFIX_LEVEL_DOCS`` 的文件名与 stage-role.md 契约 3 的
表格一一对应；修改契约时必须同步修改本文件。

**不负责**的范围：
- 不校验对人文档的"字段内容完整性"（由各角色自检）。
- 不自动补写缺失文档，只报告。
- regression 级路径暂不在 V1 校验范围内（见 change.md 风险 C）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from harness_workflow.workflow_helpers import (
    resolve_bugfix_root,
    resolve_requirement_reference,
    resolve_requirement_root,
)


# --- 契约 3 单一真相映射表 ----------------------------------------------------
#
# stage → (对人文档文件名, 粒度) 对照 stage-role.md 契约 3 表格：
#   | requirement_review | 需求摘要.md  | req    |
#   | planning           | 变更简报.md  | change |
#   | executing          | 实施说明.md  | change |
#   | testing            | 测试结论.md  | req    |
#   | acceptance         | 验收摘要.md  | req    |
#   | regression         | 回归简报.md  | regression |
#   | done               | 交付总结.md  | req    |

HUMAN_DOC_CONTRACT: dict[str, tuple[str, str]] = {
    "requirement_review": ("需求摘要.md", "req"),
    "planning": ("变更简报.md", "change"),
    "executing": ("实施说明.md", "change"),
    "testing": ("测试结论.md", "req"),
    "acceptance": ("验收摘要.md", "req"),
    "done": ("交付总结.md", "req"),
}

# req 级应产出的对人文档（落在 req 根目录）
REQ_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("requirement_review", "需求摘要.md"),
    ("testing", "测试结论.md"),
    ("acceptance", "验收摘要.md"),
    ("done", "交付总结.md"),
)

# change 级应产出的对人文档（落在每个 change 子目录）
CHANGE_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("planning", "变更简报.md"),
    ("executing", "实施说明.md"),
)

# bugfix 级应产出的对人文档（落在 bugfix 根目录）
BUGFIX_LEVEL_DOCS: tuple[tuple[str, str], ...] = (
    ("regression", "回归简报.md"),
    ("executing", "实施说明.md"),
    ("testing", "测试结论.md"),
    ("acceptance", "验收摘要.md"),
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


def _collect_req_items(req_dir: Path) -> list[ValidationItem]:
    items: list[ValidationItem] = []
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
