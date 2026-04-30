"""tests/test_install_post_message.py

chg-A（req-55 改进）: install 后输出 LLM 区段未填充时的提示句

TC-01: install --no-llm 后 stdout 含两段提示（"Claude Code 提示" + "Codex 提示"）
TC-02: install 调真 LLM（mock provider 填好内容）后 stdout 不含提示（LLM 已填充）
"""

from __future__ import annotations

import os
import re
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import render_skeleton, PLAYBOOK_ROOT_SUFFIX
from harness_workflow.playbook.llm import (
    GeneratedContent,
    LLMProvider,
    NoopProvider,
    PlaybookContext,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_python_project(root: Path, domains: list[str]) -> None:
    """建立 Python 模块结构（src/modules/*），供 infer_domains 命中 Level-1。"""
    for d in domains:
        (root / "src" / "modules" / d).mkdir(parents=True, exist_ok=True)


def _make_mock_content(domains: list[str]) -> GeneratedContent:
    """构建 mock LLM 返回内容（固定文本）。"""
    return GeneratedContent(
        overview_description="Mock project overview for testing purposes.",
        tech_decisions=["Use Python", "Use FastAPI"],
        domain_descriptions={d: f"Mock description for {d} domain." for d in domains},
        domain_keywords={d: [f"{d}-kw1", f"{d}-kw2"] for d in domains},
    )


def _make_mock_provider_filled(domains: list[str]):
    """构建 mock LLM provider，generate() 返回固定内容（模拟真实 LLM 填充）。"""
    content = _make_mock_content(domains)
    provider = MagicMock(spec=LLMProvider)
    provider.name = "MockProvider"
    provider.is_available.return_value = True
    provider.generate.return_value = content
    return provider


# ---------------------------------------------------------------------------
# TC-01: install --no-llm 后 stdout 含两段提示
# ---------------------------------------------------------------------------

def test_tc01_no_llm_stdout_contains_hints(tmp_path, capsys, monkeypatch):
    """TC-01: init_playbook(no_llm=True) → stdout 含 'Claude Code 提示' 和 'Codex 提示'。"""
    domains = ["service-a", "service-b"]
    _setup_python_project(tmp_path, domains)

    # 确保 CI env 不影响
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=True)
    assert rc == 0

    captured = capsys.readouterr()
    stdout = captured.out

    # 应该含强指令式 ASSISTANT INSTRUCTION 头
    assert "[ASSISTANT INSTRUCTION" in stdout, (
        f"Expected '[ASSISTANT INSTRUCTION' header in stdout, got:\n{stdout}"
    )
    assert "REQUIRED FOLLOW-UP" in stdout, (
        f"Expected 'REQUIRED FOLLOW-UP' in stdout, got:\n{stdout}"
    )

    # 应该含路书文件路径引用
    assert "overview.md" in stdout, (
        f"Expected 'overview.md' reference in stdout, got:\n{stdout}"
    )
    assert "domains/" in stdout, (
        f"Expected 'domains/' reference in stdout, got:\n{stdout}"
    )

    # 提示应该强调只填 LLM 区段，不碰 AUTO 区段
    assert "<!-- LLM:" in stdout, (
        f"Expected '<!-- LLM:' marker reference in stdout, got:\n{stdout}"
    )
    assert "<!-- AUTO:" in stdout, (
        f"Expected '<!-- AUTO:' marker reference (do-not-modify hint) in stdout, got:\n{stdout}"
    )

    # 提示应该指示 agent 立刻执行不要委托给用户
    assert "automatically" in stdout.lower() or "immediately" in stdout.lower(), (
        f"Expected automatic-execution directive in stdout, got:\n{stdout}"
    )


# ---------------------------------------------------------------------------
# TC-02: install 调真 LLM（mock provider 填好内容）后 stdout 不含提示
# ---------------------------------------------------------------------------

def test_tc02_with_real_llm_no_hint_output(tmp_path, capsys, monkeypatch):
    """TC-02: init_playbook(no_llm=False) + mock provider 返回内容 → stdout 不含提示句。

    mock provider 不是 NoopProvider，generate() 返回实际内容 → llm_filled=True → 不输出提示。
    """
    domains = ["core", "api"]
    _setup_python_project(tmp_path, domains)

    mock_provider = _make_mock_provider_filled(domains)

    # patch auto_detect_provider 返回 mock（非 Noop）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0

    # generate 被调用
    assert mock_provider.generate.call_count >= 1

    captured = capsys.readouterr()
    stdout = captured.out

    # 不应含提示句（LLM 已经填好了）
    assert "Claude Code 提示" not in stdout, (
        f"Expected NO 'Claude Code 提示' in stdout when LLM filled, got:\n{stdout}"
    )
    assert "Codex 提示" not in stdout, (
        f"Expected NO 'Codex 提示' in stdout when LLM filled, got:\n{stdout}"
    )
    assert "[playbook] LLM 区段未填充" not in stdout, (
        f"Expected NO LLM hint when LLM filled, got:\n{stdout}"
    )


# ---------------------------------------------------------------------------
# TC-03（bonus）: NoopProvider fallback 时也输出提示句
# ---------------------------------------------------------------------------

def test_tc03_noop_provider_fallback_shows_hint(tmp_path, capsys, monkeypatch):
    """TC-03（bonus）: auto_detect_provider 返回 NoopProvider 时（无 LLM），也应输出提示句。"""
    domains = ["module-x"]
    _setup_python_project(tmp_path, domains)

    # 返回 NoopProvider（generate 返回 None）
    noop = NoopProvider()
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: noop,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0

    captured = capsys.readouterr()
    stdout = captured.out

    # NoopProvider 未填内容，应该有强指令式提示
    assert "[ASSISTANT INSTRUCTION" in stdout, (
        f"Expected '[ASSISTANT INSTRUCTION' header when NoopProvider used, got:\n{stdout}"
    )
