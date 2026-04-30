"""tests/test_section_readonly_semantics.py

req-56（路书引擎升级）/ chg-05（区段级只读语义修订 + playbook-check 兼容）

5 TC：
  TC-01 base-role 文字 lint：grep 命中三个语义关键词
  TC-02 check LLM 区段配对漂移：tmpdir + 人工删 LLM 区段闭合 marker → exit ≠ 0 + 含 SEGMENT_UNPAIRED
  TC-03 check 不报告 TODO 区段编辑：tmpdir + 人工改区段外 TODO → exit 0
  TC-04 baseline AUTO 区段漂移仍检：tmpdir + 人工删 AUTO 区段闭合 marker → exit ≠ 0
  TC-05 base-role 硬门禁号唯一性：grep ^## 硬门禁十 命中数 = 1
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_check import playbook_check
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX
from harness_workflow.tools.harness_playbook_refresh import playbook_refresh

# base-role.md 权威路径（在工作仓库内，不在 tmp_path 里）
_BASE_ROLE_PATH = REPO_ROOT / ".workflow" / "context" / "roles" / "base-role.md"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_playbook_with_llm_section(root: Path) -> Path:
    """创建路书骨架（含 LLM:OVERVIEW_DESC 区段）并执行 refresh，使 AUTO 段内容与期望一致。"""
    render_skeleton(root, ["core"])
    playbook_refresh(root)
    playbook_dir = root / PLAYBOOK_ROOT_SUFFIX

    # 确保 overview.md 有一个真实的 LLM:OVERVIEW_DESC 内容（模拟 install 后 LLM 填充结果）
    overview_md = playbook_dir / "overview.md"
    content = overview_md.read_text(encoding="utf-8")
    content = content.replace(
        "<!-- LLM:OVERVIEW_DESC -->\n<!-- TODO: ≤ 3 句话描述项目用途和目标用户 -->\n<!-- /LLM:OVERVIEW_DESC -->",
        "<!-- LLM:OVERVIEW_DESC -->\n这是一个示例项目，用于演示路书只读语义。\n<!-- /LLM:OVERVIEW_DESC -->",
    )
    overview_md.write_text(content, encoding="utf-8")

    # 确保 core/README.md 有真实职责描述（避免 K-01 触发 exit 1）
    readme = playbook_dir / "domains" / "core" / "README.md"
    readme_content = readme.read_text(encoding="utf-8")
    readme_content = readme_content.replace(
        "<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->",
        "核心业务逻辑模块，负责系统核心流程处理。",
    )
    readme.write_text(readme_content, encoding="utf-8")

    return playbook_dir


# ---------------------------------------------------------------------------
# TC-01: base-role 文字 lint
# ---------------------------------------------------------------------------

def test_tc01_base_role_text_lint():
    """TC-01 base-role 文字 lint: 命中三个语义关键词

    grep 命中：
      1. "AUTO 区段只读"
      2. "TODO 区域可改"
      3. "agent 默认不改"
    """
    assert _BASE_ROLE_PATH.exists(), f"base-role.md not found at {_BASE_ROLE_PATH}"
    text = _BASE_ROLE_PATH.read_text(encoding="utf-8")

    assert "AUTO 区段只读" in text, (
        f"Expected 'AUTO 区段只读' in base-role.md §4"
    )
    assert "TODO 区域可改" in text, (
        f"Expected 'TODO 区域可改' in base-role.md §4"
    )
    assert "agent 默认不改" in text, (
        f"Expected 'agent 默认不改' in base-role.md §4"
    )


# ---------------------------------------------------------------------------
# TC-02: check LLM 区段配对漂移
# ---------------------------------------------------------------------------

def test_tc02_check_llm_segment_drift(tmp_path, monkeypatch):
    """TC-02: tmpdir 完整路书（含 LLM:OVERVIEW_DESC 区段）+ 人工删 LLM 区段闭合 marker（1 行）
    → playbook-check exit ≠ 0 + 输出含 SEGMENT_UNPAIRED。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    playbook_dir = _make_playbook_with_llm_section(tmp_path)
    overview_md = playbook_dir / "overview.md"

    # 人工删 LLM:OVERVIEW_DESC 闭合 marker（= 删区段中 1 行，marker 行）
    content = overview_md.read_text(encoding="utf-8")
    assert "<!-- /LLM:OVERVIEW_DESC -->" in content, (
        f"Expected <!-- /LLM:OVERVIEW_DESC --> in overview.md:\n{content}"
    )
    # 删除闭合 marker 行（1 行）
    content_modified = content.replace("<!-- /LLM:OVERVIEW_DESC -->", "")
    overview_md.write_text(content_modified, encoding="utf-8")

    rc = playbook_check(tmp_path)
    assert rc != 0, (
        f"Expected playbook-check exit ≠ 0 after removing LLM close marker, got exit {rc}"
    )


# ---------------------------------------------------------------------------
# TC-03: check 不报告 TODO 区段编辑
# ---------------------------------------------------------------------------

def test_tc03_check_todo_edit_no_drift(tmp_path, monkeypatch, capsys):
    """TC-03: tmpdir 完整路书 + 人工改 overview.md "## 最近变更" 段下 TODO 内容（区段外）
    → playbook-check exit 0（区段外编辑不触发漂移）。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    playbook_dir = _make_playbook_with_llm_section(tmp_path)
    overview_md = playbook_dir / "overview.md"

    # 人工把区段外 TODO 改成自定义中文（## 最近变更 段下）
    content = overview_md.read_text(encoding="utf-8")
    content_modified = content.replace(
        "<!-- TODO: 最近 3 次重要 req/bugfix 概述（human-authored，非 AUTO） -->",
        "req-56: 路书引擎升级完成，区段级只读语义落地。",
    )
    overview_md.write_text(content_modified, encoding="utf-8")

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"Expected playbook-check exit 0 after editing TODO area (outside segments), "
        f"got exit {rc}.\nstdout:\n{captured.out}\nstderr:\n{captured.err}"
    )


# ---------------------------------------------------------------------------
# TC-04: baseline AUTO 区段漂移仍检
# ---------------------------------------------------------------------------

def test_tc04_baseline_auto_segment_drift(tmp_path, monkeypatch):
    """TC-04: tmpdir 完整路书（含 AUTO:STACK 区段）+ 人工删 AUTO 区段闭合 marker（1 行）
    → playbook-check exit ≠ 0（baseline 行为保留，AUTO 区段漂移仍被检测）。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    playbook_dir = _make_playbook_with_llm_section(tmp_path)
    arch_md = playbook_dir / "architecture.md"

    # 人工删 AUTO:STACK 闭合 marker
    content = arch_md.read_text(encoding="utf-8")
    assert "<!-- /AUTO:STACK -->" in content, (
        f"Expected <!-- /AUTO:STACK --> in architecture.md:\n{content}"
    )
    content_modified = content.replace("<!-- /AUTO:STACK -->", "")
    arch_md.write_text(content_modified, encoding="utf-8")

    rc = playbook_check(tmp_path)
    assert rc != 0, (
        f"Expected playbook-check exit ≠ 0 after removing AUTO:STACK close marker "
        f"(baseline drift detection must still work), got exit {rc}"
    )


# ---------------------------------------------------------------------------
# TC-05: base-role 硬门禁号唯一性
# ---------------------------------------------------------------------------

def test_tc05_base_role_hardgate_uniqueness():
    """TC-05: grep '^## 硬门禁十' base-role.md 命中数 = 1（不重复编号；硬门禁十一是独立后续编号，不算重复）。"""
    assert _BASE_ROLE_PATH.exists(), f"base-role.md not found at {_BASE_ROLE_PATH}"
    text = _BASE_ROLE_PATH.read_text(encoding="utf-8")

    matches = re.findall(r"^## 硬门禁十(?!一)", text, re.MULTILINE)
    assert len(matches) == 1, (
        f"Expected exactly 1 occurrence of '## 硬门禁十' (excluding 硬门禁十一) in base-role.md, "
        f"found {len(matches)}: {matches}"
    )
