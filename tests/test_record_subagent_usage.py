"""Tests for chg-08（stage 耗时 + token 消耗统计 + usage-reporter 对人报告）/ Scope-A.

覆盖 record_subagent_usage helper：
- 追加到 .workflow/state/sessions/{req-id}/usage-log.yaml（YAML list append）
- 同步写 feedback.jsonl subagent_usage 事件
- 无 req_id 时静默返回（不写文件）
- 多次调用正确追加多条记录
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


class RecordSubagentUsageTest(unittest.TestCase):
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

    def test_usage_log_yaml_created(self) -> None:
        """record_subagent_usage 应在 sessions/{req-id}/usage-log.yaml 写入记录。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="req-39",
            stage="executing",
            chg_id="chg-08",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-39" / "usage-log.yaml"
        self.assertTrue(log_path.exists(), "usage-log.yaml 应被创建")
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("role: executing", content)
        self.assertIn("model: sonnet", content)
        self.assertIn("stage: executing", content)
        self.assertIn("chg_id: chg-08", content)
        self.assertIn("input_tokens: 100", content)
        self.assertIn("output_tokens: 50", content)
        self.assertIn("total_tokens: 175", content)
        self.assertIn("tool_uses: 3", content)
        self.assertIn("duration_ms: 2500", content)

    def test_usage_log_yaml_appends_multiple(self) -> None:
        """record_subagent_usage 多次调用应 append 到同一文件。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="req-39",
            stage="executing",
        )
        record_subagent_usage(
            self.root,
            role="testing",
            model="sonnet",
            usage={"input_tokens": 200, "output_tokens": 80, "total_tokens": 280,
                   "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                   "tool_uses": 5, "duration_ms": 3000},
            req_id="req-39",
            stage="testing",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-39" / "usage-log.yaml"
        content = log_path.read_text(encoding="utf-8")
        self.assertIn("role: executing", content)
        self.assertIn("role: testing", content)
        self.assertIn("stage: testing", content)
        # 两条记录都存在
        self.assertGreaterEqual(content.count("- ts:"), 2, "应有 2 条 YAML list item")

    def test_no_req_id_silently_returns(self) -> None:
        """req_id 为空时，record_subagent_usage 应静默返回，不创建文件。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="",
        )
        sessions_dir = self.root / ".workflow" / "state" / "sessions"
        yaml_files = list(sessions_dir.rglob("usage-log.yaml"))
        self.assertEqual(len(yaml_files), 0, "req_id 为空时不应创建 usage-log.yaml")

    def test_feedback_jsonl_subagent_usage_written(self) -> None:
        """record_subagent_usage 应同步写 feedback.jsonl subagent_usage 事件。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="executing",
            model="sonnet",
            usage=self._usage(),
            req_id="req-39",
            stage="executing",
            chg_id="chg-08",
            reg_id=None,
        )
        feedback_path = self.root / ".workflow" / "state" / "feedback" / "feedback.jsonl"
        self.assertTrue(feedback_path.exists(), "feedback.jsonl 应被创建")
        lines = [ln for ln in feedback_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertGreaterEqual(len(lines), 1, "应有至少一条 feedback 事件")
        entry = json.loads(lines[-1])
        self.assertEqual(entry["event"], "subagent_usage")
        data = entry["data"]
        self.assertEqual(data["role"], "executing")
        self.assertEqual(data["model"], "sonnet")
        self.assertEqual(data["chg_id"], "chg-08")
        self.assertEqual(data["req_id"], "req-39")
        self.assertEqual(data["usage"]["input_tokens"], 100)

    def test_usage_log_starts_with_list_item(self) -> None:
        """usage-log.yaml 的每条记录应以 '- ts:' 开头（YAML list 格式）。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="acceptance",
            model="sonnet",
            usage=self._usage(),
            req_id="req-40",
            stage="acceptance",
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-40" / "usage-log.yaml"
        content = log_path.read_text(encoding="utf-8")
        self.assertTrue(
            content.lstrip().startswith("- ts:"),
            "usage-log.yaml 第一行应以 '- ts:' 开头（YAML list item）"
        )

    def test_optional_fields_absent_when_not_provided(self) -> None:
        """chg_id / reg_id / stage 为 None 时，对应字段不应出现在 yaml 记录中。"""
        from harness_workflow.workflow_helpers import record_subagent_usage

        record_subagent_usage(
            self.root,
            role="regression",
            model="opus",
            usage=self._usage(),
            req_id="req-39",
            # stage=None (default), chg_id=None (default), reg_id=None (default)
        )
        log_path = self.root / ".workflow" / "state" / "sessions" / "req-39" / "usage-log.yaml"
        content = log_path.read_text(encoding="utf-8")
        self.assertNotIn("stage:", content)
        self.assertNotIn("chg_id:", content)
        self.assertNotIn("reg_id:", content)


if __name__ == "__main__":
    unittest.main()
