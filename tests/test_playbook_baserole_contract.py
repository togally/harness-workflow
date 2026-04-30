"""
tests/test_playbook_baserole_contract.py

chg-02（baseRole代码加载规则与CLAUDE索引）contract tests.
Validates that base-role.md contains 硬门禁十 and CLAUDE.md has 项目路书 index section.

TC-01: base-role.md 含 ## 硬门禁十：代码加载规则 标题 + 顶部清单含"硬门禁十"行
TC-02: grep '^## 硬门禁' 命中数 >= 8（原 7 + 新 1）
TC-03: CLAUDE.md 末尾含 ## 项目路书 段 + 路径含 artifacts/project/playbooks/
TC-04（可选）: scaffold_v2 mirror 同步 — mirror base-role.md 也含硬门禁十
"""

from pathlib import Path
import re

REPO_ROOT = Path(__file__).parent.parent
BASE_ROLE = REPO_ROOT / ".workflow" / "context" / "roles" / "base-role.md"
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
MIRROR_BASE_ROLE = (
    REPO_ROOT
    / "src"
    / "harness_workflow"
    / "assets"
    / "scaffold_v2"
    / ".workflow"
    / "context"
    / "roles"
    / "base-role.md"
)


def test_tc01_baserole_has_gate10_title_and_checklist_entry():
    """TC-01: base-role.md 含 ## 硬门禁十：代码加载规则 标题 + 顶部清单含"硬门禁十"行"""
    content = BASE_ROLE.read_text(encoding="utf-8")

    # 标题命中
    assert "## 硬门禁十：代码加载规则" in content, (
        "base-role.md 缺少 '## 硬门禁十：代码加载规则' 标题"
    )

    # 顶部清单命中：在 **硬门禁清单** 段落内必须有"硬门禁十"
    checklist_match = re.search(
        r"\*\*硬门禁清单\*\*：(.*?)(?=^##\s)", content, re.DOTALL | re.MULTILINE
    )
    assert checklist_match is not None, "找不到 **硬门禁清单** 段落"
    checklist_section = checklist_match.group(1)
    assert "硬门禁十" in checklist_section, (
        "**硬门禁清单** 段落中缺少硬门禁十条目"
    )


def test_tc02_baserole_has_at_least_8_gate_headers():
    """TC-02: grep '^## 硬门禁' 命中数 >= 8（原 7 + 新 1）"""
    content = BASE_ROLE.read_text(encoding="utf-8")
    gate_headers = re.findall(r"^## 硬门禁", content, re.MULTILINE)
    count = len(gate_headers)
    assert count >= 8, (
        f"base-role.md 中 '## 硬门禁' 标题数为 {count}，期望 >= 8"
    )


def test_tc03_claude_md_has_playbook_index_section():
    """TC-03: CLAUDE.md 含 ## 项目路书 段 + 路径含 artifacts/project/playbooks/"""
    content = CLAUDE_MD.read_text(encoding="utf-8")

    # 含 ## 项目路书
    assert re.search(r"^## 项目路书", content, re.MULTILINE), (
        "CLAUDE.md 缺少 '## 项目路书' 段"
    )

    # 路径 artifacts/project/playbooks/ 至少出现一次
    playbooks_refs = re.findall(r"artifacts/project/playbooks", content)
    assert len(playbooks_refs) >= 1, (
        f"CLAUDE.md 中 'artifacts/project/playbooks' 命中数为 {len(playbooks_refs)}，期望 >= 1"
    )

    # 4 份核心文件均提及
    for fname in ("overview.md", "architecture.md", "code-map.md", "runbook.md"):
        assert fname in content, f"CLAUDE.md 项目路书索引节缺少 '{fname}'"


def test_tc04_scaffold_mirror_synced():
    """TC-04（可选）: scaffold_v2 mirror base-role.md 也含硬门禁十"""
    if not MIRROR_BASE_ROLE.exists():
        import pytest
        pytest.skip("scaffold_v2 mirror base-role.md 不存在，跳过")

    mirror_content = MIRROR_BASE_ROLE.read_text(encoding="utf-8")

    assert "## 硬门禁十：代码加载规则" in mirror_content, (
        "scaffold_v2 mirror base-role.md 缺少 '## 硬门禁十：代码加载规则' 标题"
    )

    checklist_match = re.search(
        r"\*\*硬门禁清单\*\*：(.*?)(?=^##\s)", mirror_content, re.DOTALL | re.MULTILINE
    )
    assert checklist_match is not None, "scaffold_v2 mirror 找不到 **硬门禁清单** 段落"
    checklist_section = checklist_match.group(1)
    assert "硬门禁十" in checklist_section, (
        "scaffold_v2 mirror **硬门禁清单** 段落中缺少硬门禁十条目"
    )
