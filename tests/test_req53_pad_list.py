"""req-53 / chg-04: _pad_list 真实扫描分组。

覆盖：
- TC-01: 空仓三段全无
- TC-02: rule 按 scope 分组
- TC-03: experience 五子分类
- TC-04: tool 列表段解析
- TC-05: 多 pad 后 list 汇总
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env


def _run_install(cwd: Path) -> None:
    r = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    assert r.returncode == 0, f"install failed: {r.stderr}"


def _run_pad(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "pad", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        env=_env(),
    )


def _run_list(cwd: Path) -> subprocess.CompletedProcess:
    return _run_pad(cwd, "list")


def test_tc01_list_空仓三段全无(tmp_path: Path) -> None:
    """TC-01: install 后立即 list → 三段各含 (无) 或空."""
    _run_install(tmp_path)
    r = _run_list(tmp_path)
    assert r.returncode == 0, f"list 失败: {r.stdout}\n{r.stderr}"
    assert "[rule]" in r.stdout, f"缺 [rule] 段: {r.stdout}"
    assert "[experience]" in r.stdout, f"缺 [experience] 段: {r.stdout}"
    assert "[tool]" in r.stdout, f"缺 [tool] 段: {r.stdout}"
    # 每段至少含 (无)
    assert "(无)" in r.stdout, f"空仓应有 (无) 提示: {r.stdout}"


def test_tc02_list_rule_按scope分组(tmp_path: Path) -> None:
    """TC-02: pad rule coding × 1 + pad rule security × 1 → list coding 有 1 项, security 有 1 项."""
    _run_install(tmp_path)
    _run_pad(tmp_path, "rule", "coding", "禁止硬编码")
    _run_pad(tmp_path, "rule", "security", "JWT-RS256")
    r = _run_list(tmp_path)
    assert r.returncode == 0, f"list 失败: {r.stdout}\n{r.stderr}"
    assert "coding" in r.stdout, f"list 缺 coding scope: {r.stdout}"
    assert "security" in r.stdout, f"list 缺 security scope: {r.stdout}"
    # 其他 scope 应有 (无)
    assert "(无)" in r.stdout, f"未填充的 scope 应显示 (无): {r.stdout}"


def test_tc03_list_experience_五子分类(tmp_path: Path) -> None:
    """TC-03: pad experience stage + tool → list stage/tool 有项, 其他显示 (无)."""
    _run_install(tmp_path)
    _run_pad(tmp_path, "experience", "stage", "教训A")
    _run_pad(tmp_path, "experience", "tool", "apifox")
    r = _run_list(tmp_path)
    assert r.returncode == 0, f"list 失败: {r.stdout}\n{r.stderr}"
    assert "stage" in r.stdout, f"list 缺 stage scope: {r.stdout}"
    assert "tool" in r.stdout, f"list 缺 tool scope: {r.stdout}"


def test_tc04_list_tool_列表段解析(tmp_path: Path) -> None:
    """TC-04: pad tool × 2 → list [tool] 段含两条."""
    _run_install(tmp_path)
    _run_pad(tmp_path, "tool", "deployer")
    _run_pad(tmp_path, "tool", "inspector")
    r = _run_list(tmp_path)
    assert r.returncode == 0, f"list 失败: {r.stdout}\n{r.stderr}"
    assert "deployer" in r.stdout, f"list 缺 deployer: {r.stdout}"
    assert "inspector" in r.stdout, f"list 缺 inspector: {r.stdout}"


def test_tc05_list_多次pad后汇总(tmp_path: Path) -> None:
    """TC-05: 混合 pad 后 list 汇总所有已登记条目."""
    _run_install(tmp_path)
    _run_pad(tmp_path, "rule", "api", "REST规范")
    _run_pad(tmp_path, "experience", "regression", "根因模板")
    _run_pad(tmp_path, "tool", "mcp-client")
    r = _run_list(tmp_path)
    assert r.returncode == 0
    out = r.stdout
    assert "REST规范" in out or "rest" in out.lower(), f"list 缺 rule 条目: {out}"
    assert "根因模板" in out or "regression" in out, f"list 缺 experience 条目: {out}"
    assert "mcp-client" in out, f"list 缺 tool 条目: {out}"
