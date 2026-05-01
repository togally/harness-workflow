"""tests/test_check_scope_limited.py

chg-F bug-3：C-01/C-04 扫描范围限定（不扫 .workflow/ 下文档）

TC-01: .workflow/ 下文档的示例 marker 不报 C-01/C-04
TC-02: 真路书文件中 unpaired marker 仍报
TC-03: .workflow/ 下 harness-manager.md 中的 AUTO:STACK 示例不误报
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_check import check_c01_auto_segment_pairs


def _make_playbook_root(root: Path) -> Path:
    """创建 artifacts/project/playbooks/ 结构（含完整 overview.md）。"""
    pb_root = root / "artifacts" / "project" / "playbooks"
    pb_root.mkdir(parents=True, exist_ok=True)
    # 写一个完整的 overview.md（无 unpaired marker）
    (pb_root / "overview.md").write_text(
        "# Overview\n"
        "<!-- AUTO:DOMAIN_LIST -->\n"
        "domain list\n"
        "<!-- /AUTO:DOMAIN_LIST -->\n",
        encoding="utf-8",
    )
    return pb_root


def _make_workflow_dir(root: Path) -> Path:
    """创建 .workflow/context/roles/ 结构。"""
    roles_dir = root / ".workflow" / "context" / "roles"
    roles_dir.mkdir(parents=True, exist_ok=True)
    return roles_dir


# ---------------------------------------------------------------------------
# TC-01: .workflow/ 下文档的示例 marker 不报 C-01/C-04
# ---------------------------------------------------------------------------

def test_tc01_workflow_docs_not_scanned(tmp_path):
    """TC-01: .workflow/ 下 md 文件中的示例 marker（unpaired）不被 C-01/C-04 报告。"""
    pb_root = _make_playbook_root(tmp_path)
    roles_dir = _make_workflow_dir(tmp_path)

    # 写一个 base-role.md 含示例 marker（unpaired，但这是说明文本）
    (roles_dir / "base-role.md").write_text(
        "# Base Role\n\n"
        "路书中使用 `<!-- AUTO:STACK -->` 作为自动区段标记示例。\n"
        "还有 `<!-- AUTO:LAYOUT -->` 等。\n"
        "注意：这些只是文档说明，不是真实 marker。\n",
        encoding="utf-8",
    )

    result = check_c01_auto_segment_pairs(tmp_path, pb_root)
    assert result.passed, (
        f"TC-01: .workflow/ 下示例 marker 不应报 SEGMENT_UNPAIRED，但得到 issues: {result.issues}"
    )


# ---------------------------------------------------------------------------
# TC-02: 真路书文件中 unpaired marker 仍报
# ---------------------------------------------------------------------------

def test_tc02_real_playbook_unpaired_still_reported(tmp_path):
    """TC-02: 真路书文件（overview.md）中有 unpaired AUTO:X → C-01/C-04 仍报告。"""
    pb_root = _make_playbook_root(tmp_path)

    # 覆盖 overview.md，写入 unpaired marker（有开无闭）
    (pb_root / "overview.md").write_text(
        "# Overview\n"
        "<!-- AUTO:DOMAIN_LIST -->\n"
        "domain list\n"
        "<!-- /AUTO:DOMAIN_LIST -->\n"
        "<!-- AUTO:ORPHAN_OPEN -->\n"
        "this is unpaired\n"
        # 注意：没有 <!-- /AUTO:ORPHAN_OPEN -->
        ,
        encoding="utf-8",
    )

    result = check_c01_auto_segment_pairs(tmp_path, pb_root)
    assert not result.passed, (
        f"TC-02: 真路书文件中 unpaired marker 应报 SEGMENT_UNPAIRED，但 passed=True. issues={result.issues}"
    )
    orphan_issues = [i for i in result.issues if "ORPHAN_OPEN" in i]
    assert len(orphan_issues) >= 1, (
        f"TC-02: 应报 ORPHAN_OPEN unpaired，但 issues={result.issues}"
    )


# ---------------------------------------------------------------------------
# TC-03: harness-manager.md 中的 <!-- AUTO:STACK --> 示例引用不误报
# ---------------------------------------------------------------------------

def test_tc03_harness_manager_example_not_reported(tmp_path):
    """TC-03: .workflow/ 下 harness-manager.md 中引用 <!-- AUTO:STACK --> 示例不误报 C-01/C-04。"""
    pb_root = _make_playbook_root(tmp_path)
    roles_dir = _make_workflow_dir(tmp_path)

    # 模拟 harness-manager.md 中的命令说明（含 AUTO marker 文字引用）
    (roles_dir / "harness-manager.md").write_text(
        "# harness-manager\n\n"
        "## 路书维护\n\n"
        "路书文件含 `<!-- AUTO:STACK -->` ... `<!-- /AUTO:STACK -->` 区段。\n"
        "以及 `<!-- AUTO:LAYOUT -->` ... `<!-- /AUTO:LAYOUT -->` 区段。\n"
        "这些是文档中的文字说明，不是真实 marker。\n",
        encoding="utf-8",
    )

    result = check_c01_auto_segment_pairs(tmp_path, pb_root)
    assert result.passed, (
        f"TC-03: harness-manager.md 示例文字不应报 SEGMENT_UNPAIRED，但 issues: {result.issues}"
    )
