"""req-53（新增-harness-命令-给项目添加规范-经验-工具-引导式）/ chg-01: CLI 入口 + 反非法 lint。

覆盖：
- TC-01: pad rule coding 解析（stub 阶段：stub 已被 chg-02 替换为真实实现，直接验 exit=0 + 文件落位）
- TC-02: pad experience stage 解析
- TC-03: pad tool（位置参数 normalize）
- TC-04: 非法 kind ABORT
- TC-05: 非法 rule scope ABORT
- TC-06: 非法 experience scope ABORT
- TC-07: pad list 分流
- TC-08: pad 裸跑 → interactive（非 TTY abort）
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
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    assert result.returncode == 0, f"install failed: {result.stderr}"


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


def test_tc01_pad_rule_coding_parsed(tmp_path: Path) -> None:
    """TC-01: pad rule coding → exit=0 (chg-02 실装後は落位まで確認)."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "禁止硬编码")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    # 文件应落位
    target = tmp_path / "artifacts" / "project" / "constraints" / "coding" / "禁止硬编码.md"
    assert target.exists(), f"文件未落位: {target}"


def test_tc02_pad_experience_stage_parsed(tmp_path: Path) -> None:
    """TC-02: pad experience stage → exit=0 + 文件落位."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "experience", "stage", "executing-虚报教训")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    target = tmp_path / "artifacts" / "project" / "experience" / "stage" / "executing-虚报教训.md"
    assert target.exists(), f"文件未落位: {target}"


def test_tc03_pad_tool_no_scope_normalize(tmp_path: Path) -> None:
    """TC-03: pad tool <title> → scope 位 normalize → exit=0 + 文件落位."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "tool", "petmall-deployer")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    target = tmp_path / "artifacts" / "project" / "tools" / "petmall-deployer.md"
    assert target.exists(), f"文件未落位: {target}"


def test_tc04_illegal_kind_abort(tmp_path: Path) -> None:
    """TC-04: pad foo → exit≠0 + stderr 含错误提示."""
    r = _run_pad(tmp_path, "foo", "bar", "baz")
    assert r.returncode != 0, f"期望非零退出码，实际 stdout={r.stdout}\nstderr={r.stderr}"
    assert "kind 必须是 rule/experience/tool" in r.stderr, f"错误信息不匹配: {r.stderr}"


def test_tc05_illegal_rule_scope_abort(tmp_path: Path) -> None:
    """TC-05: pad rule standards → exit≠0 + stderr 含 rule scope 错误."""
    r = _run_pad(tmp_path, "rule", "standards", "X")
    assert r.returncode != 0, f"期望非零退出码，实际 stdout={r.stdout}\nstderr={r.stderr}"
    assert "rule scope 必须是" in r.stderr or "scope 必须是" in r.stderr, \
        f"错误信息不匹配: {r.stderr}"
    assert "coding" in r.stderr, f"错误信息应含 coding: {r.stderr}"


def test_tc06_illegal_experience_scope_abort(tmp_path: Path) -> None:
    """TC-06: pad experience standards → exit≠0 + stderr 含 experience scope 错误."""
    r = _run_pad(tmp_path, "experience", "standards", "X")
    assert r.returncode != 0, f"期望非零退出码，实际 stdout={r.stdout}\nstderr={r.stderr}"
    assert "scope 必须是" in r.stderr, f"错误信息不匹配: {r.stderr}"
    assert "roles" in r.stderr, f"错误信息应含 roles: {r.stderr}"


def test_tc07_pad_list_stub(tmp_path: Path) -> None:
    """TC-07: pad list → exit=0 + stdout 含分组标识."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "list")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    assert "[rule]" in r.stdout or "Project-level Catalog" in r.stdout, \
        f"list 输出未含分组标识: {r.stdout}"


def test_tc08_pad_empty_interactive_non_tty(tmp_path: Path) -> None:
    """TC-08: 裸跑 pad（非 TTY）→ stderr 含 interactive 提示 + exit≠0."""
    # 不传任何参数，stdin 关闭（非 TTY）
    r = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "pad"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        encoding="utf-8",
        env=_env(),
        stdin=subprocess.DEVNULL,  # 强制非 TTY
    )
    assert r.returncode != 0, f"期望非零退出码（非 TTY interactive abort），实际 stdout={r.stdout}\nstderr={r.stderr}"
    assert "interactive" in r.stderr or "TTY" in r.stderr or "interactive 模式" in r.stderr, \
        f"stderr 应含 interactive 提示: {r.stderr}"
