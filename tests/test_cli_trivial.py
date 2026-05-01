"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-01（trivial 通道命令骨架）
tests/test_cli_trivial.py — harness trivial CLI 子进程单测（TC-Dogfood-01 / TC-12）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml


def _init_harness_repo(tmpdir: Path) -> None:
    """最小 harness repo 初始化。"""
    wf_state = tmpdir / ".workflow" / "state"
    wf_state.mkdir(parents=True, exist_ok=True)
    (wf_state / "runtime.yaml").write_text(
        "operation_type: requirement\n"
        "operation_target: ''\n"
        "current_requirement: ''\n"
        "current_requirement_title: ''\n"
        "stage: ''\n"
        "conversation_mode: open\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        "active_requirements: []\n",
        encoding="utf-8",
    )
    (wf_state / "requirements").mkdir(parents=True, exist_ok=True)
    (tmpdir / ".workflow" / "context").mkdir(parents=True, exist_ok=True)
    codex_dir = tmpdir / ".codex" / "harness"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "config.json").write_text('{"language": "cn"}', encoding="utf-8")
    (codex_dir / "managed-files.json").write_text("{}", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=str(tmpdir), capture_output=True)


_ROOT = Path(__file__).resolve().parents[1]


def _run_harness(tmpdir: Path, *args: str) -> subprocess.CompletedProcess:
    import os
    cmd = [sys.executable, "-m", "harness_workflow.cli"] + list(args) + ["--root", str(tmpdir)]
    env = {**os.environ, "PYTHONPATH": str(_ROOT / "src")}
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmpdir), env=env)


class TestCliTrivial:
    """TC-Dogfood-01：harness trivial CLI 端到端测试。"""

    def test_trivial_command_exits_zero(self, tmp_path):
        """harness trivial "test" exit 0"""
        _init_harness_repo(tmp_path)
        result = _run_harness(tmp_path, "trivial", "test 修 typo")
        assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"

    def test_stdout_contains_id_and_title(self, tmp_path):
        """TC-10：stdout 含 trivial-{id}（{title}）格式"""
        _init_harness_repo(tmp_path)
        result = _run_harness(tmp_path, "trivial", "修复测试 typo")
        assert result.returncode == 0
        assert "修复测试 typo" in result.stdout, f"stdout 需含 title，实际: {result.stdout}"
        # trivial-define appears in path as "trivial-define" or in stage as "trivial_define"
        assert "trivial" in result.stdout.lower(), f"stdout 需含 trivial 关键词，实际: {result.stdout}"

    def test_runtime_yaml_updated(self, tmp_path):
        """runtime.yaml task_type=trivial + stage=trivial_define"""
        _init_harness_repo(tmp_path)
        result = _run_harness(tmp_path, "trivial", "runtime 测试")
        assert result.returncode == 0

        runtime_path = tmp_path / ".workflow" / "state" / "runtime.yaml"
        runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8"))
        assert runtime.get("operation_type") == "trivial", f"operation_type 应为 trivial，实际: {runtime}"
        assert runtime.get("stage") == "trivial_define", f"stage 应为 trivial_define，实际: {runtime}"

    def test_trivial_no_title_returns_error(self, tmp_path):
        """TC-12（反例）：不传 title → 错误退出"""
        _init_harness_repo(tmp_path)
        result = _run_harness(tmp_path, "trivial")
        # 无 title 应该报错（returncode != 0 或 stdout/stderr 含 error）
        assert result.returncode != 0 or "required" in (result.stderr + result.stdout).lower()
