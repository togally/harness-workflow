"""tests/conftest.py

req-56（路书引擎升级）/ chg-04（install/refresh 集成 LLM）
autouse fixture：ensure_no_real_llm

每个测试自动 monkeypatch：
  - ANTHROPIC_API_KEY / OPENAI_API_KEY env 为空
  - harness_workflow.playbook.llm.auto_detect_provider 返回 NoopProvider()
防止任何测试意外调用真 LLM API。

注意：需要测试 LLM 调用的测试用例应该自行覆盖 auto_detect_provider 的 mock。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure src is importable (in-process)
_SRC = str(Path(__file__).resolve().parents[1] / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# Ensure subprocesses can also import harness_workflow (no install required)
_existing_pp = os.environ.get("PYTHONPATH", "")
if _SRC not in _existing_pp.split(os.pathsep):
    os.environ["PYTHONPATH"] = _SRC + (os.pathsep + _existing_pp if _existing_pp else "")


@pytest.fixture(autouse=True)
def ensure_no_real_llm(monkeypatch):
    """全局 autouse fixture：清空 LLM API key + 让 auto_detect_provider 返回 NoopProvider。

    这样所有测试默认不会发出真实 LLM API 请求，除非测试自己显式 override 此 fixture。
    """
    from harness_workflow.playbook.llm import NoopProvider

    # 清空 API key 环境变量（防止真实 API 调用）
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # monkeypatch auto_detect_provider 返回 NoopProvider（安全兜底）
    monkeypatch.setattr(
        "harness_workflow.playbook.llm.auto_detect_provider",
        lambda *args, **kwargs: NoopProvider(),
    )

    yield
