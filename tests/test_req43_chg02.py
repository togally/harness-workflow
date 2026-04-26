"""Tests for req-43（交付总结完善）/ chg-02（补齐 stage 流转点 entered_at + exited_at 时间戳）.

覆盖 _sync_stage_to_state_yaml prev_stage 参数 + archive_requirement 兜底补 done.entered_at：
- TC-01: 正向流转 entered_at + exited_at 配对
- TC-02: 跨 stage 跳跃流转
- TC-03: prev_stage=None 兼容老调用方
- TC-04: 二次流转不覆盖既有 entered_at
- TC-05: archive 兜底补 done.entered_at
- TC-06: archive 兜底 + 上一 stage._exited_at
- TC-07: _backfill_done_timestamps 无 stage_timestamps 时安全跳过
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_minimal_repo(root: Path) -> None:
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)


def _write_state_yaml(root: Path, req_id: str, stage: str = "planning") -> Path:
    from harness_workflow.workflow_helpers import save_simple_yaml
    state_dir = root / ".workflow" / "state" / "requirements"
    yaml_path = state_dir / f"{req_id}.yaml"
    save_simple_yaml(yaml_path, {
        "id": req_id,
        "title": "test req",
        "stage": stage,
        "stage_timestamps": {"planning": "2026-04-25T10:00:00+00:00"},
    })
    return yaml_path


class ForwardTransitionTest(unittest.TestCase):
    """TC-01: 正向流转 entered_at + exited_at 配对."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_entered_exited_pair(self) -> None:
        from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml
        _write_state_yaml(self.root, "req-99", "planning")
        _sync_stage_to_state_yaml(
            self.root, "requirement", "req-99", "executing",
            prev_stage="planning",
        )
        yaml_path = self.root / ".workflow" / "state" / "requirements" / "req-99.yaml"
        state = load_simple_yaml(yaml_path)
        ts = state.get("stage_timestamps", {})
        self.assertIn("executing", ts, "executing entered_at 应写入")
        self.assertIn("planning_exited_at", ts, "planning_exited_at 应写入")


class JumpTransitionTest(unittest.TestCase):
    """TC-02: 跨 stage 跳跃流转（planning → done）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_jump_transition(self) -> None:
        from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml
        _write_state_yaml(self.root, "req-99", "planning")
        _sync_stage_to_state_yaml(
            self.root, "requirement", "req-99", "done",
            prev_stage="planning",
        )
        yaml_path = self.root / ".workflow" / "state" / "requirements" / "req-99.yaml"
        state = load_simple_yaml(yaml_path)
        ts = state.get("stage_timestamps", {})
        self.assertIn("done", ts, "done entered_at 应写入")
        self.assertIn("planning_exited_at", ts, "planning_exited_at 应写入")
        # 中间 stage（executing 等）不应伪造
        self.assertNotIn("executing", ts, "跳跃时 executing 不应伪造")


class PrevStageNoneCompatTest(unittest.TestCase):
    """TC-03: prev_stage=None 兼容老调用方（只写 new_stage entered_at）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_no_prev_stage(self) -> None:
        from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml
        _write_state_yaml(self.root, "req-99", "planning")
        _sync_stage_to_state_yaml(
            self.root, "requirement", "req-99", "executing"
            # prev_stage omitted → None
        )
        yaml_path = self.root / ".workflow" / "state" / "requirements" / "req-99.yaml"
        state = load_simple_yaml(yaml_path)
        ts = state.get("stage_timestamps", {})
        self.assertIn("executing", ts, "executing entered_at 应写入")
        # 无 prev_stage，不应写 *_exited_at
        exited_keys = [k for k in ts if k.endswith("_exited_at")]
        self.assertEqual(exited_keys, [], "未传 prev_stage 时不应写 *_exited_at")


class NoCoverExistingEnteredAtTest(unittest.TestCase):
    """TC-04: 二次流转不覆盖既有 entered_at."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_no_overwrite_existing(self) -> None:
        from harness_workflow.workflow_helpers import (
            _sync_stage_to_state_yaml, load_simple_yaml, save_simple_yaml,
        )
        yaml_path = _write_state_yaml(self.root, "req-99", "executing")
        # 首次写入 executing
        _sync_stage_to_state_yaml(
            self.root, "requirement", "req-99", "executing", prev_stage="planning",
        )
        state = load_simple_yaml(yaml_path)
        first_ts = state["stage_timestamps"]["executing"]
        # 再次流转 executing（模拟重复调用）
        _sync_stage_to_state_yaml(
            self.root, "requirement", "req-99", "executing", prev_stage="planning",
        )
        state2 = load_simple_yaml(yaml_path)
        self.assertEqual(
            state2["stage_timestamps"]["executing"], first_ts,
            "二次流转不应覆盖既有 entered_at",
        )


class ArchiveBackfillDoneTest(unittest.TestCase):
    """TC-05: _backfill_done_timestamps 补 done.entered_at."""

    def test_backfill_done_entered_at(self) -> None:
        from harness_workflow.workflow_helpers import _backfill_done_timestamps
        state = {
            "id": "req-99",
            "stage": "acceptance",
            "stage_timestamps": {
                "planning": "2026-04-25T10:00:00+00:00",
                "executing": "2026-04-25T11:00:00+00:00",
                "acceptance": "2026-04-25T12:00:00+00:00",
            },
        }
        _backfill_done_timestamps(state)
        ts = state["stage_timestamps"]
        self.assertIn("done", ts, "done.entered_at 应被补填")


class ArchiveBackfillExitedAtTest(unittest.TestCase):
    """TC-06: _backfill_done_timestamps 补上一 stage._exited_at."""

    def test_backfill_prev_stage_exited_at(self) -> None:
        from harness_workflow.workflow_helpers import _backfill_done_timestamps
        state = {
            "id": "req-99",
            "stage": "acceptance",
            "stage_timestamps": {
                "planning": "2026-04-25T10:00:00+00:00",
                "acceptance": "2026-04-25T12:00:00+00:00",
            },
        }
        _backfill_done_timestamps(state)
        ts = state["stage_timestamps"]
        self.assertIn("acceptance_exited_at", ts, "acceptance_exited_at 应被补填")


class BackfillNoStageTimestampsTest(unittest.TestCase):
    """TC-07: 无 stage_timestamps 时安全跳过."""

    def test_no_stage_timestamps_safe(self) -> None:
        from harness_workflow.workflow_helpers import _backfill_done_timestamps
        state = {"id": "req-legacy", "stage": "done"}
        _backfill_done_timestamps(state)  # should not raise
        # No stage_timestamps added since none existed
        self.assertNotIn("stage_timestamps", state)


if __name__ == "__main__":
    unittest.main()
