"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-01（trivial 通道命令骨架）
tests/test_create_trivial.py — create_trivial helper 单测（TC-07）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from harness_workflow.workflow_helpers import create_trivial, load_requirement_runtime


def _init_harness_repo(tmpdir: Path) -> None:
    """最小 harness repo 初始化（仿 test_create_requirement_flat 模式）。"""
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
    # ensure_harness_root 需要 .workflow/context
    (tmpdir / ".workflow" / "context").mkdir(parents=True, exist_ok=True)
    # .codex/harness/config.json 供 ensure_config
    codex_dir = tmpdir / ".codex" / "harness"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "config.json").write_text('{"language": "cn"}', encoding="utf-8")
    (codex_dir / "managed-files.json").write_text("{}", encoding="utf-8")
    # git init
    subprocess.run(["git", "init"], cwd=str(tmpdir), capture_output=True)
    subprocess.run(["git", "checkout", "-b", "main"], cwd=str(tmpdir), capture_output=True)


class TestCreateTrivial:
    """TC-07：create_trivial 单测。"""

    def test_creates_flow_dir_and_files(self, tmp_path):
        """TC-07a：目录创建 + requirement.md 含 trivial frontmatter"""
        _init_harness_repo(tmp_path)
        rc = create_trivial(tmp_path, "修 typo")
        assert rc == 0

        # 找到新建的 req 目录
        flow_reqs = list((tmp_path / ".workflow" / "flow" / "requirements").iterdir())
        assert len(flow_reqs) >= 1
        req_dir = flow_reqs[0]

        req_md = req_dir / "requirement.md"
        assert req_md.exists(), "requirement.md 必须存在"
        content = req_md.read_text(encoding="utf-8")
        assert "task_type: trivial" in content, "requirement.md 需含 task_type: trivial"

    def test_trivial_spec_placeholder_created(self, tmp_path):
        """trivial-define/trivial-spec.md 占位文件存在"""
        _init_harness_repo(tmp_path)
        create_trivial(tmp_path, "测试 trivial")

        flow_reqs = list((tmp_path / ".workflow" / "flow" / "requirements").iterdir())
        req_dir = flow_reqs[0]
        spec = req_dir / "trivial-define" / "trivial-spec.md"
        assert spec.exists(), "trivial-spec.md 占位文件必须存在"

    def test_runtime_yaml_task_type_trivial(self, tmp_path):
        """TC-07c：runtime.yaml task_type=trivial, stage=trivial_define"""
        _init_harness_repo(tmp_path)
        create_trivial(tmp_path, "测试 trivial 运行时")

        runtime = load_requirement_runtime(tmp_path)
        assert runtime.get("operation_type") == "trivial"
        assert runtime.get("stage") == "trivial_define"

    def test_state_yaml_created(self, tmp_path):
        """state yaml 写入正确字段"""
        _init_harness_repo(tmp_path)
        create_trivial(tmp_path, "state yaml 测试")

        state_files = list((tmp_path / ".workflow" / "state" / "requirements").iterdir())
        assert len(state_files) >= 1
        state_data = yaml.safe_load(state_files[0].read_text(encoding="utf-8"))
        assert state_data.get("task_type") == "trivial"
        assert state_data.get("stage") == "trivial_define"

    def test_empty_title_raises(self, tmp_path):
        """空 title 抛 SystemExit"""
        _init_harness_repo(tmp_path)
        with pytest.raises(SystemExit):
            create_trivial(tmp_path, "")
