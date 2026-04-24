"""req-38（api-document-upload 工具闭环：触发门禁 + MCP pre-check 协议 + 存量项目同步）/ chg-05（存量项目同步验证 + _template 可选段 + 契约合规）：
install_repo 对 tools/protocols/ 路径 propagate 行为 + 白名单不含 protocols 的回归保护。

AC-8 覆盖：
  test_install_repo_propagates_protocols_dir：
    tmp_path 存量项目（旧版 .workflow/，无 protocols/）跑 install_repo 后，
    .workflow/tools/protocols/mcp-precheck.md 被创建且内容与 scaffold_v2 mirror 一致。
  test_scaffold_v2_mirror_whitelist_excludes_protocols：
    _SCAFFOLD_V2_MIRROR_WHITELIST 中不包含 "tools/protocols/" 路径，
    确保 protocols 子目录受硬门禁五保护，不被豁免同步。
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    SCAFFOLD_V2_ROOT,
    _SCAFFOLD_V2_MIRROR_WHITELIST,
    install_repo,
)


def _git_init(root: Path) -> None:
    """最小 git 初始化（install_repo 内部依赖 git status 等命令）。"""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_install_repo_propagates_protocols_dir(tmp_path, monkeypatch):
    """req-38（api-document-upload 工具闭环）/ chg-05（存量项目同步验证）AC-8 test 1：
    在存量 harness 项目（.workflow/ 已存在但无 protocols/ 子目录）执行 install_repo 后，
    断言 .workflow/tools/protocols/mcp-precheck.md 被创建，内容与 scaffold_v2 mirror 一致。
    """
    # 防止触发本仓库 self-audit 噪声
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 初始化 git 环境
    _git_init(tmp_path)

    # 模拟存量项目：创建基础 .workflow/ 结构，但不包含 protocols/ 子目录
    workflow_dir = tmp_path / ".workflow"
    workflow_dir.mkdir()
    tools_dir = workflow_dir / "tools"
    tools_dir.mkdir()
    catalog_dir = tools_dir / "catalog"
    catalog_dir.mkdir()
    # 存量项目有旧版 _template.md（无前置检查段）
    (catalog_dir / "_template.md").write_text(
        "# 工具：{名称}\n\n## 适用场景\n\n## 注意事项\n",
        encoding="utf-8",
    )
    # 确认 protocols/ 不存在（模拟存量）
    assert not (tools_dir / "protocols").exists(), "sanity: protocols/ must not exist before install"

    # 执行 install_repo（存量项目升级路径）
    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0, f"install_repo returned non-zero: {rc}"

    # 断言 mcp-precheck.md 被创建
    protocols_dir = tmp_path / ".workflow" / "tools" / "protocols"
    mcp_precheck = protocols_dir / "mcp-precheck.md"
    assert protocols_dir.exists(), (
        "install_repo must create .workflow/tools/protocols/ in legacy project"
    )
    assert mcp_precheck.exists(), (
        "install_repo must propagate mcp-precheck.md to .workflow/tools/protocols/"
    )

    # 断言内容与 scaffold_v2 mirror 一致
    mirror_mcp_precheck = (
        SCAFFOLD_V2_ROOT / ".workflow" / "tools" / "protocols" / "mcp-precheck.md"
    )
    assert mirror_mcp_precheck.exists(), "scaffold_v2 mirror must contain mcp-precheck.md (sanity)"
    expected = mirror_mcp_precheck.read_text(encoding="utf-8")
    actual = mcp_precheck.read_text(encoding="utf-8")
    assert actual == expected, (
        "propagated mcp-precheck.md must match scaffold_v2 mirror content"
    )


def test_scaffold_v2_mirror_whitelist_excludes_protocols(tmp_path):
    """req-38（api-document-upload 工具闭环）/ chg-05（存量项目同步验证）AC-8 test 2：
    _SCAFFOLD_V2_MIRROR_WHITELIST 不包含 "tools/protocols/" 路径，
    确保 protocols 子目录不被豁免同步（受硬门禁五保护）。
    """
    # 断言白名单中无 "tools/protocols/" 条目
    assert "tools/protocols/" not in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        "tools/protocols/ must NOT be in _SCAFFOLD_V2_MIRROR_WHITELIST — "
        "protocols/ must be sync-protected by 硬门禁五, not whitelisted"
    )

    # 额外验证：白名单中的任何条目都不应匹配 tools/protocols/mcp-precheck.md
    test_path = "tools/protocols/mcp-precheck.md"
    matching = [w for w in _SCAFFOLD_V2_MIRROR_WHITELIST if w in test_path]
    assert matching == [], (
        f"No whitelist entry should match '{test_path}', but got: {matching}"
    )
