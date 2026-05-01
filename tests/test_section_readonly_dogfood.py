"""tests/test_section_readonly_dogfood.py

req-56（路书引擎升级）/ chg-05（区段级只读语义修订 + playbook-check 兼容）

TC-Dogfood-01: 区段级只读完整语义 dogfood 测试

  tmp_path + install 完整路书（mock LLM 填充 LLM:OVERVIEW_DESC）
  + 三种修改场景 + subprocess playbook-check + 断言：
    场景 a（仅 TODO 区段编辑）→ check exit 0
    场景 b（LLM 区段被人为删闭合 marker）→ check exit ≠ 0
    场景 c（AUTO 区段被人为删闭合 marker）→ check exit ≠ 0
  + runtime.yaml stage 字段存在
  + feedback.jsonl ≥ 1 事件（如果存在）

注意：conftest.py autouse ensure_no_real_llm 全局生效；
本测试进程内调 init_playbook，自行 override auto_detect_provider 返回 MockProvider。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
from harness_workflow.playbook.llm import GeneratedContent, LLMProvider


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_env() -> dict:
    """构建子进程环境变量（CI=true 跳过 LLM）。"""
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing_pp}" if existing_pp else SRC_DIR
    env["CI"] = "true"
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    return env


def _run_playbook_check(tmp_path: Path) -> subprocess.CompletedProcess:
    """subprocess 调 CLI playbook-check --root <tmp_path>。"""
    return subprocess.run(
        [
            sys.executable, "-m", "harness_workflow.cli",
            "playbook-check", "--root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
        env=_make_env(),
    )


def _read_llm_section(file_path: Path, marker: str) -> str:
    """提取 LLM 区段内容（不含 marker 行）。"""
    content = file_path.read_text(encoding="utf-8")
    m = re.search(
        rf"<!-- LLM:{re.escape(marker)} -->(.*?)<!-- /LLM:{re.escape(marker)} -->",
        content,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------
# TC-Dogfood-01
# ---------------------------------------------------------------------------

def test_section_readonly_full_semantics(tmp_path, monkeypatch):
    """TC-Dogfood-01: 区段级只读完整语义 dogfood 测试。

    步骤：
      1. 在进程内调 init_playbook（注入 mock LLM），生成路书骨架 + LLM 填充
      2. 场景 a：改区段外 TODO（## 最近变更 段下）→ check exit 0
      3. 场景 b：删 LLM:OVERVIEW_DESC 闭合 marker（1 行）→ check exit ≠ 0
      4. 场景 c（在 b 修复后）：删 AUTO:STACK 闭合 marker（1 行）→ check exit ≠ 0
      5. runtime.yaml stage 字段存在（如果存在）
      6. feedback.jsonl 事件数 ≥ 1（如果存在）
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # ------------------------------------------------------------------
    # 1. 设置进程内 mock LLM，调 init_playbook
    # ------------------------------------------------------------------
    domains = ["core", "api"]

    content_obj = GeneratedContent(
        overview_description="示例项目：用于验证区段级只读语义。",
        tech_decisions=["Python 3.11", "pytest", "harness-workflow"],
        domain_descriptions={
            "core": "核心业务逻辑模块，负责系统核心流程处理。",
            "api": "API 网关模块，负责路由与鉴权。",
        },
        domain_keywords={
            "core": ["core", "business", "logic"],
            "api": ["api", "gateway", "auth"],
        },
    )

    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.name = "MockProvider"
    mock_provider.is_available.return_value = True
    mock_provider.generate.return_value = content_obj

    # override auto_detect_provider（init.py 从 llm 模块 import）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *a, **kw: mock_provider,
    )
    monkeypatch.delenv("CI", raising=False)

    from harness_workflow.playbook.init import init_playbook
    from harness_workflow.tools.harness_playbook_refresh import playbook_refresh

    # 使用 override_domains 跳过推断器，直接指定领域列表（确保骨架生成成功）
    rc_install = init_playbook(tmp_path, override_domains=domains)
    assert rc_install == 0, f"init_playbook returned {rc_install}"

    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), "playbook dir should exist after install"

    # 运行 playbook_refresh 使 AUTO 段内容与期望一致（消除骨架初始漂移）
    playbook_refresh(tmp_path)

    # LLM:OVERVIEW_DESC 应已被 mock LLM 填充
    overview_md = playbook_dir / "overview.md"
    assert overview_md.exists(), "overview.md should exist"
    overview_desc = _read_llm_section(overview_md, "OVERVIEW_DESC")
    assert "示例项目" in overview_desc or overview_desc != "", (
        f"Expected LLM OVERVIEW_DESC to be filled, got: {overview_desc!r}"
    )

    # 确保 core/README.md 有真实职责描述（避免 K-01 触发 exit 1 干扰场景 a）
    for domain in domains:
        readme = playbook_dir / "domains" / domain / "README.md"
        if readme.exists():
            readme_content = readme.read_text(encoding="utf-8")
            if "<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->" in readme_content:
                readme_content = readme_content.replace(
                    "<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->",
                    f"{domain} 模块负责平台对应业务服务。",
                )
                readme.write_text(readme_content, encoding="utf-8")

    # ------------------------------------------------------------------
    # 场景 a：改区段外 TODO → check exit 0
    # ------------------------------------------------------------------
    overview_content = overview_md.read_text(encoding="utf-8")
    overview_content_a = overview_content.replace(
        "<!-- TODO: 最近 3 次重要 req/bugfix 概述（human-authored，非 AUTO） -->",
        "req-56: 路书引擎升级完成，区段级只读语义落地。",
    )
    overview_md.write_text(overview_content_a, encoding="utf-8")

    result_a = _run_playbook_check(tmp_path)
    assert result_a.returncode == 0, (
        f"场景 a：TODO 区外编辑应 exit 0，实际 exit {result_a.returncode}.\n"
        f"stdout:\n{result_a.stdout}\nstderr:\n{result_a.stderr}"
    )

    # ------------------------------------------------------------------
    # 场景 b：删 LLM:OVERVIEW_DESC 闭合 marker（1 行）→ check exit ≠ 0
    # ------------------------------------------------------------------
    content_b = overview_md.read_text(encoding="utf-8")
    assert "<!-- /LLM:OVERVIEW_DESC -->" in content_b, (
        f"Expected <!-- /LLM:OVERVIEW_DESC --> in overview.md after install"
    )
    content_b_modified = content_b.replace("<!-- /LLM:OVERVIEW_DESC -->", "")
    overview_md.write_text(content_b_modified, encoding="utf-8")

    result_b = _run_playbook_check(tmp_path)
    assert result_b.returncode != 0, (
        f"场景 b：LLM 区段闭合 marker 删除后应 exit ≠ 0，实际 exit {result_b.returncode}.\n"
        f"stdout:\n{result_b.stdout}\nstderr:\n{result_b.stderr}"
    )

    # ------------------------------------------------------------------
    # 场景 c：修复 b + 删 AUTO:STACK 闭合 marker → check exit ≠ 0
    # ------------------------------------------------------------------
    # 先恢复 overview.md（修复场景 b）
    overview_md.write_text(content_b, encoding="utf-8")

    arch_md = playbook_dir / "architecture.md"
    assert arch_md.exists(), "architecture.md should exist"
    content_c = arch_md.read_text(encoding="utf-8")
    assert "<!-- /AUTO:STACK -->" in content_c, (
        f"Expected <!-- /AUTO:STACK --> in architecture.md"
    )
    content_c_modified = content_c.replace("<!-- /AUTO:STACK -->", "")
    arch_md.write_text(content_c_modified, encoding="utf-8")

    result_c = _run_playbook_check(tmp_path)
    assert result_c.returncode != 0, (
        f"场景 c：AUTO 区段闭合 marker 删除后应 exit ≠ 0，实际 exit {result_c.returncode}.\n"
        f"stdout:\n{result_c.stdout}\nstderr:\n{result_c.stderr}"
    )

    # ------------------------------------------------------------------
    # runtime.yaml stage 字段存在（如 install 写入）
    # ------------------------------------------------------------------
    runtime_yaml = tmp_path / ".workflow" / "state" / "runtime.yaml"
    if runtime_yaml.exists():
        runtime_text = runtime_yaml.read_text(encoding="utf-8")
        assert "stage" in runtime_text, (
            f"Expected 'stage' field in runtime.yaml:\n{runtime_text}"
        )

    # ------------------------------------------------------------------
    # feedback.jsonl 事件数 ≥ 1（如果存在）
    # ------------------------------------------------------------------
    feedback_jsonl = tmp_path / ".workflow" / "state" / "feedback.jsonl"
    if feedback_jsonl.exists():
        lines = [
            line for line in feedback_jsonl.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(lines) >= 1, (
            f"Expected ≥1 event in feedback.jsonl, got {len(lines)}: {lines}"
        )
