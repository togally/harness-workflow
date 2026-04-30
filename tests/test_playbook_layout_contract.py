"""req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-01（路书目录骨架契约）

契约文档骨架验证：
- TC-01：.workflow/flow/playbook-layout.md 存在且含 ≥ 5 个二级标题（## ）
- TC-02：.workflow/flow/playbook-layout.md 含 ≥ 5 类 AUTO 区段定义（<!-- AUTO:）
- TC-03：.workflow/flow/playbook-layout.md §1 前 10 行含字面量 artifacts/project/playbooks/
- TC-04：.workflow/flow/repository-layout.md §2.1 段含 playbooks 关键字 + 4 类描述
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK_LAYOUT = REPO_ROOT / ".workflow" / "flow" / "playbook-layout.md"
REPO_LAYOUT = REPO_ROOT / ".workflow" / "flow" / "repository-layout.md"


def test_playbook_layout_md_exists_and_sections_complete() -> None:
    """TC-01：playbook-layout.md 存在，且含 ≥ 5 个二级标题（## ）"""
    assert PLAYBOOK_LAYOUT.exists(), f"playbook-layout.md 不存在：{PLAYBOOK_LAYOUT}"
    content = PLAYBOOK_LAYOUT.read_text(encoding="utf-8")
    section_count = sum(1 for line in content.splitlines() if line.startswith("## "))
    assert section_count >= 5, (
        f"期望 ≥ 5 个二级标题（## ），实际命中 {section_count} 个；"
        f"AC-01.1 要求 §1-§5 共 5 节"
    )


def test_auto_section_marker_definitions_listed() -> None:
    """TC-02：playbook-layout.md §4 列出 ≥ 5 类 AUTO 区段定义"""
    assert PLAYBOOK_LAYOUT.exists(), f"playbook-layout.md 不存在：{PLAYBOOK_LAYOUT}"
    content = PLAYBOOK_LAYOUT.read_text(encoding="utf-8")
    auto_marker_count = content.count("<!-- AUTO:")
    assert auto_marker_count >= 5, (
        f"期望 ≥ 5 类 AUTO 区段标记（<!-- AUTO:），实际命中 {auto_marker_count} 个；"
        f"AC-01.2 要求 §4 列出 STACK / SCRIPTS / LAYOUT / DOMAIN_FILES / DOMAIN_LIST 五类"
    )


def test_section1_declares_playbook_root_path() -> None:
    """TC-03：playbook-layout.md §1 前 10 行含字面量 artifacts/project/playbooks/（OQ-1=B）"""
    assert PLAYBOOK_LAYOUT.exists(), f"playbook-layout.md 不存在：{PLAYBOOK_LAYOUT}"
    lines = PLAYBOOK_LAYOUT.read_text(encoding="utf-8").splitlines()
    first_10 = "\n".join(lines[:10])
    assert "artifacts/project/playbooks/" in first_10, (
        f"§1 前 10 行未找到字面量 'artifacts/project/playbooks/'；"
        f"OQ-1=B 决策要求 §1 顶部第一行显式声明路书根目录。\n前 10 行内容：\n{first_10}"
    )


def test_repository_layout_section21_extended_to_4_types() -> None:
    """TC-04：repository-layout.md §2.1 段含 playbooks 关键字 + 4 类描述"""
    assert REPO_LAYOUT.exists(), f"repository-layout.md 不存在：{REPO_LAYOUT}"
    content = REPO_LAYOUT.read_text(encoding="utf-8")

    # 找到 §2.1 段落
    lines = content.splitlines()
    section_21_start = None
    section_21_end = None
    for i, line in enumerate(lines):
        if "### 2.1" in line and section_21_start is None:
            section_21_start = i
        elif section_21_start is not None and line.startswith("###") and i > section_21_start:
            section_21_end = i
            break
    assert section_21_start is not None, "未找到 §2.1 段落"

    section_21_text = "\n".join(
        lines[section_21_start: section_21_end if section_21_end else section_21_start + 80]
    )

    # 验证 playbooks 关键字存在
    assert "playbooks" in section_21_text, (
        f"§2.1 段落未找到 'playbooks' 关键字；"
        f"req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-01（路书目录骨架契约）要求豁免从 3 类扩到 4 类（+ playbooks）"
    )

    # 验证四类描述（constraints / experience / tools / playbooks 均存在）
    for keyword in ["constraints", "experience", "tools", "playbooks"]:
        assert keyword in section_21_text, (
            f"§2.1 段落未找到 '{keyword}' 关键字；"
            f"期望 4 类（constraints / experience / tools / playbooks）均出现在 §2.1"
        )
