"""req-49（工作流轻量级通道：trivial 任务（几行代码）走简化流程）/ chg-01（trivial 通道命令骨架）
tests/test_suggest_apply_trivial.py — harness suggest --apply --trivial 单测（TC-08 / TC-Dogfood-03）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from harness_workflow.workflow_helpers import (
    apply_suggestion_as_trivial,
    load_requirement_runtime,
)


def _init_harness_repo(tmpdir: Path) -> None:
    wf_state = tmpdir / ".workflow" / "state"
    wf_state.mkdir(parents=True, exist_ok=True)
    (wf_state / "runtime.yaml").write_text(
        "operation_type: requirement\noperation_target: ''\ncurrent_requirement: ''\n"
        "current_requirement_title: ''\nstage: ''\nconversation_mode: open\n"
        "locked_requirement: ''\nlocked_requirement_title: ''\nlocked_stage: ''\n"
        "current_regression: ''\ncurrent_regression_title: ''\n"
        "ff_mode: false\nff_stage_history: []\nactive_requirements: []\n",
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


def _create_sug(tmpdir: Path, sug_id: str = "sug-01", title: str = "测试建议") -> Path:
    """在 tmpdir 创建最小 sug 文件。"""
    sug_dir = tmpdir / ".workflow" / "flow" / "suggestions"
    sug_dir.mkdir(parents=True, exist_ok=True)
    sug_file = sug_dir / f"{sug_id}.md"
    sug_file.write_text(
        f"---\nid: {sug_id}\ntitle: {title}\nstatus: pending\n---\n\n{title} 内容。\n",
        encoding="utf-8",
    )
    return sug_file


class TestApplySuggestionAsTrivial:
    """TC-08：apply_suggestion_as_trivial helper 单测。"""

    def test_runtime_task_type_is_trivial(self, tmp_path):
        """TC-08：apply --trivial 后 runtime task_type=trivial"""
        _init_harness_repo(tmp_path)
        _create_sug(tmp_path, "sug-01", "测试建议标题")
        rc = apply_suggestion_as_trivial(tmp_path, "sug-01")
        assert rc == 0
        runtime = load_requirement_runtime(tmp_path)
        assert runtime.get("operation_type") == "trivial"
        assert runtime.get("stage") == "trivial_define"

    def test_sug_archived_after_apply(self, tmp_path):
        """sug 文件被归档"""
        _init_harness_repo(tmp_path)
        sug_path = _create_sug(tmp_path, "sug-02", "建议归档测试")
        apply_suggestion_as_trivial(tmp_path, "sug-02")
        assert not sug_path.exists(), "sug 文件应已移到 archive/"
        archive_path = tmp_path / ".workflow" / "flow" / "suggestions" / "archive" / "sug-02.md"
        assert archive_path.exists(), "archive/sug-02.md 应存在"

    def test_nonexistent_sug_raises(self, tmp_path):
        """不存在的 sug-id → SystemExit"""
        _init_harness_repo(tmp_path)
        # ensure suggestions dir exists so we get "not found" not "No suggestions found"
        (tmp_path / ".workflow" / "flow" / "suggestions").mkdir(parents=True, exist_ok=True)
        with pytest.raises(SystemExit):
            apply_suggestion_as_trivial(tmp_path, "sug-999")
