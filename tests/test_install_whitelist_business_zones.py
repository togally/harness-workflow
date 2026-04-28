"""bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）/
chg-02（self-audit 白名单补 3 个业务态目录）dogfood 测试用例。

覆盖范围：
- TC-02：tmpdir 创建 flow/bugfixes/、context/experience/regression/、context/experience/risk/ 三类文件
  → _install_self_audit + _sync_scaffold_v2_mirror_to_live silent skip；drift count 不增
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    _SCAFFOLD_V2_MIRROR_WHITELIST,
    _install_self_audit,
    _sync_scaffold_v2_mirror_to_live,
)


def test_whitelist_contains_three_new_entries() -> None:
    """AC-02-a：_SCAFFOLD_V2_MIRROR_WHITELIST 含 flow/bugfixes / context/experience/regression /
    context/experience/risk 三条。
    """
    assert "flow/bugfixes" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        "flow/bugfixes should be in _SCAFFOLD_V2_MIRROR_WHITELIST (bugfix-8 / chg-02)"
    )
    assert "context/experience/regression" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        "context/experience/regression should be in _SCAFFOLD_V2_MIRROR_WHITELIST"
    )
    assert "context/experience/risk" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        "context/experience/risk should be in _SCAFFOLD_V2_MIRROR_WHITELIST"
    )


def test_tc02_business_files_silent_skip_self_audit(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-02：tmpdir 创建三类业务态文件，跑 _install_self_audit → silent skip（drift count 不包含这些文件）。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 确保不触发 dev-mode（tmp_path 无 pyproject.toml / src/harness_workflow）
    business_files = [
        ".workflow/flow/bugfixes/bugfix-99-test/bugfix.md",
        ".workflow/context/experience/regression/reg-99.md",
        ".workflow/context/experience/risk/test.md",
    ]
    for rel in business_files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {rel}\n", encoding="utf-8")

    drift = _install_self_audit(tmp_path)
    captured = capsys.readouterr()

    # 这三个文件不应被计为 drift（白名单覆盖）
    for rel in business_files:
        assert rel not in captured.err, (
            f"Business-state file {rel!r} should NOT appear in self-audit drift output; "
            f"got stderr:\n{captured.err!r}"
        )

    # drift 总数不应因这三个文件增加（可能有其它非白名单文件 drift，但这三个不算）
    # 用子集检测：stderr 中不含这三个文件路径
    # （因为 tmpdir 不含模板文件，可能有其它 drift，但不包含业务态路径）
    for rel in business_files:
        rel_short = rel.replace(".workflow/", "")
        assert rel_short not in captured.err, (
            f"Business-state substring {rel_short!r} should NOT appear in self-audit stderr"
        )


def test_tc02_business_files_not_reverse_cleaned(tmp_path: Path) -> None:
    """TC-02 变体：业务态文件在 _sync_scaffold_v2_mirror_to_live 中不被反向清理。"""
    business_files = [
        (".workflow/flow/bugfixes/bugfix-99-test/bugfix.md", "# bugfix-99 test"),
        (".workflow/context/experience/regression/reg-99.md", "# reg-99 experience"),
        (".workflow/context/experience/risk/test.md", "# risk test"),
    ]
    for rel, content in business_files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    actions = _sync_scaffold_v2_mirror_to_live(tmp_path, check=False, force_managed=False)

    # 断言：所有业务态文件仍然存在（未被反向清理）
    for rel, content in business_files:
        p = tmp_path / rel
        assert p.exists(), f"Business-state file should be preserved: {rel}"
        assert p.read_text(encoding="utf-8") == content, f"Content changed: {rel}"

    # actions 中不应包含这三个文件路径的 "archived stale" 记录
    action_str = " ".join(actions)
    for rel, _ in business_files:
        assert rel not in action_str or "archived stale" not in action_str or (
            rel not in " ".join(a for a in actions if "archived" in a)
        ), f"Business-state file {rel} should not be in archived stale actions"
