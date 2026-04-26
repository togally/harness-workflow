"""Tests for req-43（交付总结完善）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））.

覆盖 record_subagent_usage helper task_type 参数：
- TC-01: task_type 默认值写入 "req"
- TC-02: task_type 显式传 "bugfix"
- TC-03: task_type 显式传 "sug"
- TC-04: req_id 为空时 noop（不写文件）
- TC-05: entries schema 完整性（含 task_type 字段）
- TC-06: feedback.jsonl 同步含 task_type 字段
- TC-07: scaffold mirror diff = 0（harness-manager.md）
- TC-08: sug-25 status = applied
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_minimal_repo(root: Path) -> None:
    """Create minimal harness repo structure for testing."""
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)


class TaskTypeDefaultTest(unittest.TestCase):
    """TC-01: task_type 默认值 → 写入 "req"."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def _usage(self) -> dict:
        return {
            "input_tokens": 100,
            "output_tokens": 50,
            "cache_read_input_tokens": 20,
            "cache_creation_input_tokens": 5,
            "total_tokens": 175,
            "tool_uses": 3,
            "duration_ms": 2500,
        }

    def test_default_task_type_is_req(self) -> None:
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="req-99",
            stage="executing",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-99" / "usage-log.yaml"
        self.assertTrue(log_path.exists())
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("task_type: req", content)


class TaskTypeBugfixTest(unittest.TestCase):
    """TC-02: task_type 显式传 "bugfix" → entry 写入 bugfix-7 目录."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def _usage(self) -> dict:
        return {
            "input_tokens": 200,
            "output_tokens": 80,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "total_tokens": 280,
            "tool_uses": 5,
            "duration_ms": 3000,
        }

    def test_explicit_bugfix_task_type(self) -> None:
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="bugfix-7",
            stage="executing",
            task_type="bugfix",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "bugfix-7" / "usage-log.yaml"
        self.assertTrue(log_path.exists(), "usage-log.yaml 应落在 bugfix-7 目录")
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("task_type: bugfix", content)


class TaskTypeSugTest(unittest.TestCase):
    """TC-03: task_type 显式传 "sug" → entry 写入 sug-30 目录."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def _usage(self) -> dict:
        return {
            "input_tokens": 50,
            "output_tokens": 20,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "total_tokens": 70,
            "tool_uses": 1,
            "duration_ms": 1000,
        }

    def test_explicit_sug_task_type(self) -> None:
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="harness-manager",
            model="opus",
            usage=self._usage(),
            req_id="sug-30",
            stage="executing",
            task_type="sug",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "sug-30" / "usage-log.yaml"
        self.assertTrue(log_path.exists(), "usage-log.yaml 应落在 sug-30 目录")
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("task_type: sug", content)


class NoopEmptyReqIdTest(unittest.TestCase):
    """TC-04: req_id 为空时 noop（不写文件）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_noop_when_req_id_empty(self) -> None:
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage={"input_tokens": 100, "total_tokens": 100},
            req_id="",
            task_type="req",
        )
        sessions_dir = self.root / ".workflow" / "state" / "sessions"
        yaml_files = list(sessions_dir.rglob("usage-log.yaml"))
        self.assertEqual(len(yaml_files), 0, "req_id 为空时不应创建任何文件")


class EntrySchemaTest(unittest.TestCase):
    """TC-05: entries schema 完整性（含 task_type 字段）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_entry_schema_complete(self) -> None:
        import yaml
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage={
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_input_tokens": 20,
                "cache_creation_input_tokens": 5,
                "total_tokens": 175,
                "tool_uses": 3,
                "duration_ms": 2500,
            },
            req_id="req-43",
            stage="executing",
            task_type="req",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-43" / "usage-log.yaml"
        data = yaml.safe_load(log_path.read_text(encoding="utf-8"))
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        entry = data[0]
        # Required fields
        self.assertIn("ts", entry)
        self.assertIn("task_type", entry)
        self.assertIn("stage", entry)
        self.assertIn("role", entry)
        self.assertIn("model", entry)
        self.assertIn("usage", entry)
        # Usage sub-fields
        usage = entry["usage"]
        for field in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                      "cache_creation_input_tokens", "total_tokens", "tool_uses", "duration_ms"):
            self.assertIn(field, usage, f"usage.{field} 应在 schema 中")


class FeedbackJsonlTaskTypeTest(unittest.TestCase):
    """TC-06: feedback.jsonl 同步含 task_type 字段."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_minimal_repo(self.root)

    def test_feedback_jsonl_has_task_type(self) -> None:
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage={"input_tokens": 100, "total_tokens": 100},
            req_id="req-43",
            stage="executing",
            task_type="req",
        )
        feedback_path = self.root / ".workflow" / "state" / "feedback" / "feedback.jsonl"
        self.assertTrue(feedback_path.exists())
        lines = [ln for ln in feedback_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        entry = json.loads(lines[-1])
        data = entry["data"]
        self.assertEqual(data.get("task_type"), "req", "feedback.jsonl data 应含 task_type=req")


class ScaffoldMirrorTest(unittest.TestCase):
    """TC-07: scaffold mirror diff = 0 (harness-manager.md + base-role.md)."""

    def test_harness_manager_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "context" / "roles" / "harness-manager.md"
        mirror = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "harness-manager.md"
        self.assertEqual(
            source.read_text(encoding="utf-8"),
            mirror.read_text(encoding="utf-8"),
            "harness-manager.md scaffold mirror 应与源文件内容相同",
        )

    def test_base_role_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "context" / "roles" / "base-role.md"
        mirror = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "base-role.md"
        self.assertEqual(
            source.read_text(encoding="utf-8"),
            mirror.read_text(encoding="utf-8"),
            "base-role.md scaffold mirror 应与源文件内容相同",
        )


class Sug25StatusTest(unittest.TestCase):
    """TC-08: sug-25 status = applied."""

    def test_sug25_applied(self) -> None:
        sug_path = REPO_ROOT / ".workflow" / "flow" / "suggestions" / "sug-25-record-subagent-usage.md"
        content = sug_path.read_text(encoding="utf-8")
        self.assertIn("status: applied", content, "sug-25 应已被标记为 applied")


if __name__ == "__main__":
    unittest.main()
