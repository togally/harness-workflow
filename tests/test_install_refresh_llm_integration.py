"""tests/test_install_refresh_llm_integration.py

req-56（路书引擎升级）/ chg-04（install/refresh 集成 LLM）
LLM 集成测试（6 TC）：

TC-01 install 调 LLM generate（mock provider 被调 ≥1 次 + 区段被替换）
TC-02 install --no-llm 跳过（mock provider 0 调用 + 区段保留 TODO）
TC-03 install env CI=true 自动跳过（同 TC-02，_resolve_no_llm 路径）
TC-04 LLM NetworkError fallback（stderr WARN + exit 0 + 区段保留 TODO）
TC-05 refresh 替换 LLM 区段（mock provider + playbook_refresh → LLM 区段内容被替换）
TC-06 多语言项目集成（Maven 多模块 fixture + mock LLM → domain README 被填充）
"""
from __future__ import annotations

import json
import os
import re
import sys
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

def _make_mock_content(domains: list[str]) -> GeneratedContent:
    """构建 mock LLM 返回内容（固定文本）。"""
    return GeneratedContent(
        overview_description="Mock project overview for testing purposes.",
        tech_decisions=["Use Python", "Use FastAPI", "Use PostgreSQL"],
        domain_descriptions={d: f"Mock description for {d} domain." for d in domains},
        domain_keywords={d: [f"{d}-kw1", f"{d}-kw2"] for d in domains},
    )


def _make_mock_provider(domains: list[str] | None = None):
    """构建 mock LLM provider，generate() 返回固定内容。"""
    if domains is None:
        domains = ["core", "api"]

    content = _make_mock_content(domains)

    provider = MagicMock(spec=LLMProvider)
    provider.name = "MockProvider"
    provider.is_available.return_value = True
    provider.generate.return_value = content
    return provider


def _setup_python_project(root: Path, domains: list[str]) -> None:
    """建立 Python 模块结构（src/modules/*），供 infer_domains 命中 Level-1。"""
    for d in domains:
        (root / "src" / "modules" / d).mkdir(parents=True, exist_ok=True)


def _read_llm_section(file_path: Path, marker: str) -> str:
    """从文件提取 <!-- LLM:MARKER --> ... <!-- /LLM:MARKER --> 区段内容（不含标记行）。"""
    content = file_path.read_text(encoding="utf-8")
    m = re.search(
        rf"<!-- LLM:{re.escape(marker)} -->(.*?)<!-- /LLM:{re.escape(marker)} -->",
        content,
        re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return ""


# ---------------------------------------------------------------------------
# TC-01: install 调 LLM（mock provider generate 被调 + 区段被替换）
# ---------------------------------------------------------------------------

def test_tc01_install_calls_llm_and_fills_sections(tmp_path, monkeypatch):
    """TC-01: init_playbook 不传 no_llm → auto_detect_provider 返回 mock → generate 被调 ≥1 次
    → overview.md LLM:OVERVIEW_DESC 区段内容 != TODO 占位。
    """
    domains = ["core", "api"]
    _setup_python_project(tmp_path, domains)

    mock_provider = _make_mock_provider(domains)

    # patch harness_workflow.playbook.llm.auto_detect_provider（init.py 从此 import）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )

    # 确保 CI env 不影响
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0

    # mock provider.generate 至少被调 1 次
    assert mock_provider.generate.call_count >= 1, (
        f"Expected generate() to be called ≥1 time, got {mock_provider.generate.call_count}"
    )

    # overview.md LLM:OVERVIEW_DESC 区段内容应被替换（不再是 TODO 占位）
    overview_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "overview.md"
    assert overview_md.exists()

    section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "Mock project overview" in section, (
        f"Expected mock content in OVERVIEW_DESC, got: {section!r}"
    )

    # 同样验证某个 domain README.md 的 DOMAIN_DESC 被填充
    domain_readme = tmp_path / PLAYBOOK_ROOT_SUFFIX / "domains" / "core" / "README.md"
    if domain_readme.exists():
        domain_section = _read_llm_section(domain_readme, "DOMAIN_DESC")
        assert "Mock description for core" in domain_section, (
            f"Expected mock domain desc in DOMAIN_DESC, got: {domain_section!r}"
        )


# ---------------------------------------------------------------------------
# TC-02: install --no-llm 跳过（mock provider 0 调用 + 区段保留 TODO 占位）
# ---------------------------------------------------------------------------

def test_tc02_install_no_llm_skips_llm(tmp_path, monkeypatch):
    """TC-02: init_playbook(no_llm=True) → generate 0 调用 + OVERVIEW_DESC 保留 TODO 占位。"""
    domains = ["core", "api"]
    _setup_python_project(tmp_path, domains)

    mock_provider = _make_mock_provider(domains)

    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=True)
    assert rc == 0

    # mock provider.generate 0 调用
    assert mock_provider.generate.call_count == 0, (
        f"Expected generate() NOT to be called with --no-llm, got {mock_provider.generate.call_count} calls"
    )

    # OVERVIEW_DESC 区段保留 TODO 占位
    overview_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "overview.md"
    assert overview_md.exists()
    section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "TODO" in section, (
        f"Expected TODO placeholder preserved with --no-llm, got: {section!r}"
    )


# ---------------------------------------------------------------------------
# TC-03: install env CI=true 自动跳过（_resolve_no_llm 路径）
# ---------------------------------------------------------------------------

def test_tc03_install_ci_env_skips_llm(tmp_path, monkeypatch):
    """TC-03: CI=true 时 init_playbook(no_llm=False) → generate 0 调用 + TODO 占位保留。"""
    domains = ["core", "api"]
    _setup_python_project(tmp_path, domains)

    mock_provider = _make_mock_provider(domains)

    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )

    # 设置 CI=true（模拟 CI 环境）
    monkeypatch.setenv("CI", "true")

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0

    # mock provider.generate 0 调用（CI=true 自动跳过）
    assert mock_provider.generate.call_count == 0, (
        f"Expected generate() NOT to be called when CI=true, got {mock_provider.generate.call_count} calls"
    )

    # OVERVIEW_DESC 区段保留 TODO 占位
    overview_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "overview.md"
    assert overview_md.exists()
    section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "TODO" in section, (
        f"Expected TODO placeholder preserved when CI=true, got: {section!r}"
    )


# ---------------------------------------------------------------------------
# TC-04: LLM NetworkError fallback（stderr WARN + exit 0 + 区段保留 TODO）
# ---------------------------------------------------------------------------

def test_tc04_llm_network_error_fallback(tmp_path, monkeypatch, capsys):
    """TC-04: mock provider.generate() raise NetworkError → stderr 含 [llm] WARN + exit 0 + TODO 保留。"""
    domains = ["core"]
    _setup_python_project(tmp_path, domains)

    # mock provider：generate() 抛异常
    failing_provider = MagicMock(spec=LLMProvider)
    failing_provider.name = "FailingProvider"
    failing_provider.is_available.return_value = True
    failing_provider.generate.side_effect = ConnectionError("Network error: connection refused")

    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: failing_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)

    # exit 0（LLM 失败不阻塞主流程）
    assert rc == 0, f"Expected exit 0 even on LLM failure, got {rc}"

    # stderr 含 [llm] WARN
    captured = capsys.readouterr()
    assert "[llm] WARN" in captured.err, (
        f"Expected '[llm] WARN' in stderr, got: {captured.err!r}"
    )

    # OVERVIEW_DESC 区段保留 TODO 占位
    overview_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "overview.md"
    assert overview_md.exists()
    section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "TODO" in section, (
        f"Expected TODO placeholder preserved after LLM failure, got: {section!r}"
    )


# ---------------------------------------------------------------------------
# TC-05: refresh 替换 LLM 区段
# ---------------------------------------------------------------------------

def test_tc05_refresh_replaces_llm_sections(tmp_path, monkeypatch):
    """TC-05: playbook_refresh(no_llm=False) + mock provider → LLM:OVERVIEW_DESC 区段内容被替换。"""
    domains = ["service", "repo"]

    # 建立完整路书骨架（含 LLM 区段 TODO 占位）
    render_skeleton(tmp_path, domains)

    # 确认初始状态有 TODO 占位
    overview_md = tmp_path / PLAYBOOK_ROOT_SUFFIX / "overview.md"
    initial_section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "TODO" in initial_section, f"Expected TODO in initial OVERVIEW_DESC, got: {initial_section!r}"

    mock_provider = _make_mock_provider(domains)

    # patch llm 模块中的 auto_detect_provider（_refresh_llm_sections 从此 import）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )

    # 设置 src/modules/service 和 src/modules/repo 让 infer_domains 命中
    for d in domains:
        (tmp_path / "src" / "modules" / d).mkdir(parents=True, exist_ok=True)

    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.tools.harness_playbook_refresh import playbook_refresh
    rc = playbook_refresh(tmp_path, no_llm=False)
    assert rc == 0

    # mock provider.generate 被调 ≥1 次
    assert mock_provider.generate.call_count >= 1, (
        f"Expected generate() called ≥1 time in refresh, got {mock_provider.generate.call_count}"
    )

    # OVERVIEW_DESC 区段内容被替换（包含 mock 返回的内容）
    refreshed_section = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "Mock project overview" in refreshed_section, (
        f"Expected mock content in OVERVIEW_DESC after refresh, got: {refreshed_section!r}"
    )


# ---------------------------------------------------------------------------
# TC-06: 多语言项目集成（Maven 多模块 + mock LLM → domain README 被填充）
# ---------------------------------------------------------------------------

def test_tc06_maven_multi_module_integration(tmp_path, monkeypatch):
    """TC-06: Maven 多模块 fixture + mock LLM → install 成功 + ≥3 模块 domain README 被填充。"""
    modules = ["platform-admin", "platform-user", "platform-order", "platform-product", "platform-payment"]

    # 创建父 pom.xml（含 <modules> 列表）
    modules_xml = "\n".join(f"    <module>{m}</module>" for m in modules)
    (tmp_path / "pom.xml").write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.petmall</groupId>
  <artifactId>petmall-parent</artifactId>
  <version>1.0.0</version>
  <packaging>pom</packaging>
  <modules>
{modules_xml}
  </modules>
</project>
""",
        encoding="utf-8",
    )

    # 创建每个子模块目录 + pom.xml
    for m in modules:
        (tmp_path / m).mkdir(exist_ok=True)
        (tmp_path / m / "pom.xml").write_text(
            f"<project><artifactId>{m}</artifactId></project>",
            encoding="utf-8",
        )

    mock_provider = _make_mock_provider(modules)

    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    rc = init_playbook(tmp_path, no_llm=False)
    assert rc == 0

    # generate 被调 ≥1 次
    assert mock_provider.generate.call_count >= 1, (
        f"Expected generate() to be called, got {mock_provider.generate.call_count}"
    )

    # 5 个 domain README.md 均存在
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    for module in modules:
        readme = playbook_dir / "domains" / module / "README.md"
        assert readme.exists(), f"domain README.md should exist for {module}"

    # ≥3 个 domain README.md DOMAIN_DESC 被 mock 内容填充
    filled_count = 0
    for module in modules:
        readme = playbook_dir / "domains" / module / "README.md"
        if readme.exists():
            section = _read_llm_section(readme, "DOMAIN_DESC")
            if f"Mock description for {module}" in section:
                filled_count += 1

    assert filled_count >= 3, (
        f"Expected ≥3 domain READMEs filled with mock LLM content, got {filled_count}/{len(modules)}"
    )
