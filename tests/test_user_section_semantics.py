"""tests/test_user_section_semantics.py

chg-C：路书产品规范完善 + 1.0.0 发版准备

验证 USER 区段语义：永不报漂移、marker 完整性校验、提示句正确。

TC-01 _USER_OPEN_RE 正则匹配 <!-- USER:NAME --> 标记
TC-02 USER 区段被人为修改后 playbook-check 不报漂移
TC-03 USER 区段 marker 缺失（unpaired）→ playbook-check 仍报 SEGMENT_UNPAIRED
TC-04 init.py _print_noop_fill_hint 提示句明确说不碰 USER 区段
"""
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_check import (
    _USER_OPEN_RE,
    _USER_CLOSE_RE,
    playbook_check,
)
from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX
from harness_workflow.tools.harness_playbook_refresh import playbook_refresh
from harness_workflow.playbook.init import _print_noop_fill_hint


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _make_playbook(root: Path, domains: list[str] | None = None) -> Path:
    """在 tmp_path 中创建路书骨架并执行 refresh（使 AUTO 区段内容与期望一致）。"""
    if domains is None:
        domains = []
    render_skeleton(root, domains)
    playbook_refresh(root)
    return root / PLAYBOOK_ROOT_SUFFIX


def _fill_readme_domain_desc(playbook_dir: Path, domain: str, text: str) -> None:
    """填入真实职责描述避免 K-01 干扰。"""
    readme = playbook_dir / "domains" / domain / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        content = content.replace(
            "<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->",
            text,
        )
        readme.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# TC-01: _USER_OPEN_RE 正则匹配
# ---------------------------------------------------------------------------

def test_tc01_user_open_re_matches():
    """TC-01: _USER_OPEN_RE 正则匹配 <!-- USER:NAME --> 格式标记。"""
    assert _USER_OPEN_RE.search("<!-- USER:RECENT_CHANGES -->") is not None, (
        "_USER_OPEN_RE should match <!-- USER:RECENT_CHANGES -->"
    )
    assert _USER_OPEN_RE.search("<!-- USER:PENDING_DECISIONS -->") is not None, (
        "_USER_OPEN_RE should match <!-- USER:PENDING_DECISIONS -->"
    )
    assert _USER_OPEN_RE.search("<!-- USER:HISTORY -->") is not None, (
        "_USER_OPEN_RE should match <!-- USER:HISTORY -->"
    )
    # 确保不匹配 AUTO 或 LLM
    assert _USER_OPEN_RE.search("<!-- AUTO:STACK -->") is None, (
        "_USER_OPEN_RE should NOT match <!-- AUTO:STACK -->"
    )
    assert _USER_OPEN_RE.search("<!-- LLM:OVERVIEW_DESC -->") is None, (
        "_USER_OPEN_RE should NOT match <!-- LLM:OVERVIEW_DESC -->"
    )


def test_tc01b_user_close_re_matches():
    """TC-01b: _USER_CLOSE_RE 正则匹配 <!-- /USER:NAME --> 格式标记。"""
    assert _USER_CLOSE_RE.search("<!-- /USER:RECENT_CHANGES -->") is not None, (
        "_USER_CLOSE_RE should match <!-- /USER:RECENT_CHANGES -->"
    )
    assert _USER_CLOSE_RE.search("<!-- /USER:HISTORY -->") is not None, (
        "_USER_CLOSE_RE should match <!-- /USER:HISTORY -->"
    )
    # 闭标记不匹配开标记
    assert _USER_CLOSE_RE.search("<!-- USER:RECENT_CHANGES -->") is None, (
        "_USER_CLOSE_RE should NOT match open marker <!-- USER:RECENT_CHANGES -->"
    )


# ---------------------------------------------------------------------------
# TC-02: USER 区段被人为修改后 playbook-check 不报漂移
# ---------------------------------------------------------------------------

def test_tc02_user_section_modified_no_drift(tmp_path, monkeypatch, capsys):
    """TC-02: overview.md USER:RECENT_CHANGES 区段内容被修改 → playbook-check exit 0（不报漂移）。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    playbook_dir = _make_playbook(tmp_path, domains=["core"])
    _fill_readme_domain_desc(playbook_dir, "core", "核心模块负责系统核心流程处理。")

    overview_md = playbook_dir / "overview.md"
    content = overview_md.read_text(encoding="utf-8")

    # 验证 USER:RECENT_CHANGES 区段存在
    assert "<!-- USER:RECENT_CHANGES -->" in content, (
        "overview.md should contain <!-- USER:RECENT_CHANGES -->"
    )

    # 人为修改 USER:RECENT_CHANGES 区段内容
    content_modified = content.replace(
        "<!-- TODO: 最近 3 次重要 req/bugfix 概述（human-authored，非 AUTO） -->",
        "chg-C: 路书三分类区段规范落地（AUTO/LLM/USER）。",
    )
    assert content_modified != content, "Should have replaced the TODO placeholder"
    overview_md.write_text(content_modified, encoding="utf-8")

    rc = playbook_check(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"Expected playbook-check exit 0 after modifying USER:RECENT_CHANGES section "
        f"(USER sections should never report drift), got exit {rc}.\n"
        f"stdout:\n{captured.out}\nstderr:\n{captured.err}"
    )


# ---------------------------------------------------------------------------
# TC-03: USER 区段 marker 缺失（unpaired）→ SEGMENT_UNPAIRED
# ---------------------------------------------------------------------------

def test_tc03_user_section_marker_missing_reports_unpaired(tmp_path, monkeypatch):
    """TC-03: 删除 overview.md <!-- /USER:RECENT_CHANGES --> 闭标记 → playbook-check 报 SEGMENT_UNPAIRED。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    playbook_dir = _make_playbook(tmp_path, domains=["core"])
    _fill_readme_domain_desc(playbook_dir, "core", "核心模块负责系统核心流程处理。")

    overview_md = playbook_dir / "overview.md"
    content = overview_md.read_text(encoding="utf-8")

    # 确认闭标记存在
    assert "<!-- /USER:RECENT_CHANGES -->" in content, (
        "overview.md should contain <!-- /USER:RECENT_CHANGES --> close marker"
    )

    # 删除闭标记（模拟不配对的 USER 区段）
    content_broken = content.replace("<!-- /USER:RECENT_CHANGES -->", "")
    overview_md.write_text(content_broken, encoding="utf-8")

    rc = playbook_check(tmp_path)
    assert rc != 0, (
        f"Expected playbook-check exit != 0 when USER marker is unpaired, got exit {rc}"
    )


# ---------------------------------------------------------------------------
# TC-04: init.py _print_noop_fill_hint 提示句明确说不碰 USER 区段
# ---------------------------------------------------------------------------

def test_tc04_noop_fill_hint_mentions_user_section(tmp_path, capsys):
    """TC-04: _print_noop_fill_hint 输出中明确提及 USER:* 区段不要碰。"""
    # 调用提示函数
    _print_noop_fill_hint(tmp_path)
    captured = capsys.readouterr()
    output = captured.out

    # 验证提示句包含关键指令
    assert "ASSISTANT INSTRUCTION" in output, (
        "_print_noop_fill_hint should output [ASSISTANT INSTRUCTION ...]"
    )
    assert "USER" in output, (
        "_print_noop_fill_hint should mention USER sections"
    )
    assert "AUTO" in output, (
        "_print_noop_fill_hint should mention AUTO sections"
    )
    # 确保明确说"不要碰"USER区段（英文指令版本）
    assert "Do NOT" in output or "not" in output.lower(), (
        "_print_noop_fill_hint should say not to touch USER/AUTO sections"
    )
    # 确认 LLM:* 区段列表
    assert "LLM:PROJECT_NAME" in output, (
        "_print_noop_fill_hint should list LLM:PROJECT_NAME as a section to fill"
    )
    assert "LLM:OVERVIEW_DESC" in output, (
        "_print_noop_fill_hint should list LLM:OVERVIEW_DESC"
    )
