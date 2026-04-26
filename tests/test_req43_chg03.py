"""Tests for req-43（交付总结完善）/ chg-03（per-stage 合并到 stage × role × model 单表渲染）.

覆盖 done_efficiency_aggregate helper stage_role_rows 新字段：
- TC-01: stage_role_rows 全齐（5 stage × 2 role）
- TC-02: 单 stage 缺失时其他 stage 正常
- TC-03: entries 全空时返回 _NO_DATA
- TC-04: multi-role 同 stage 多行聚合
- TC-05: 同 (stage, role, model) 多 entry 累加
- TC-06: 历史 req 旧 schema 兼容（无 task_type 字段）
- TC-07: done.md 模板含单表头（9 列）
- TC-08: scaffold mirror 同步
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_repo(root: Path) -> None:
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)


def _write_usage_log(req_dir: Path, entries: list[dict]) -> None:
    import yaml
    req_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for e in entries:
        lines.append(f"- ts: {e.get('ts', '2026-04-25T10:00:00+00:00')}")
        lines.append(f"  task_type: {e.get('task_type', 'req')}")
        if e.get("stage"):
            lines.append(f"  stage: {e['stage']}")
        lines.append(f"  role: {e.get('role', 'executing')}")
        lines.append(f"  model: {e.get('model', 'sonnet')}")
        lines.append("  usage:")
        for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                  "cache_creation_input_tokens", "total_tokens", "tool_uses", "duration_ms"):
            lines.append(f"    {k}: {e.get('usage', {}).get(k, 0)}")
        lines.append("")
    (req_dir / "usage-log.yaml").write_text("\n".join(lines) + "\n", encoding="utf-8")


class StageRoleRowsFullTest(unittest.TestCase):
    """TC-01: stage_role_rows 全齐."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_stage_role_rows_full(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        entries = []
        for stage in ["planning", "executing", "testing", "acceptance", "done"]:
            for role in ["analyst", "executing"]:
                entries.append({
                    "stage": stage, "role": role, "model": "sonnet",
                    "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150,
                              "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0,
                              "tool_uses": 2, "duration_ms": 1000},
                })
        _write_usage_log(req_dir, entries)
        result = done_efficiency_aggregate(self.root, "req-99")
        rows = result["stage_role_rows"]
        self.assertIsInstance(rows, list)
        self.assertGreaterEqual(len(rows), 10, "应有 5 stage × 2 role = 10 行")
        # Check 9 columns in each row
        for row in rows:
            for col in ("stage", "role", "model", "input_tokens", "output_tokens",
                        "cache_read_input_tokens", "cache_creation_input_tokens",
                        "total_tokens", "tool_uses"):
                self.assertIn(col, row, f"row 应含 {col}")


class SingleStageMissingTest(unittest.TestCase):
    """TC-02: 单 stage 缺失时其他 stage 正常."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_missing_one_stage(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        entries = [
            {"stage": "planning", "role": "analyst", "model": "opus",
             "usage": {"input_tokens": 100, "total_tokens": 100, "tool_uses": 1}},
            {"stage": "executing", "role": "executing", "model": "sonnet",
             "usage": {"input_tokens": 200, "total_tokens": 200, "tool_uses": 2}},
            # testing is missing
        ]
        _write_usage_log(req_dir, entries)
        result = done_efficiency_aggregate(self.root, "req-99")
        rows = result["stage_role_rows"]
        stages = [r["stage"] for r in rows]
        self.assertIn("planning", stages)
        self.assertIn("executing", stages)
        self.assertNotIn("testing", stages, "testing entries 缺失，不应在 stage_role_rows 出现")


class EmptyEntriesTest(unittest.TestCase):
    """TC-03: entries 全空时返回 _NO_DATA."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_empty_usage_log(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate, _NO_DATA
        # No usage-log.yaml
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        req_dir.mkdir(parents=True, exist_ok=True)
        result = done_efficiency_aggregate(self.root, "req-99")
        self.assertEqual(result["stage_role_rows"], _NO_DATA)


class MultiRoleSameStageTest(unittest.TestCase):
    """TC-04: multi-role 同 stage 多行聚合（不合并不同 role）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_multi_role_same_stage(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        entries = [
            {"stage": "executing", "role": "executing", "model": "sonnet",
             "usage": {"input_tokens": 100, "total_tokens": 100, "tool_uses": 1}},
            {"stage": "executing", "role": "testing", "model": "sonnet",
             "usage": {"input_tokens": 200, "total_tokens": 200, "tool_uses": 2}},
            {"stage": "executing", "role": "acceptance", "model": "opus",
             "usage": {"input_tokens": 300, "total_tokens": 300, "tool_uses": 3}},
        ]
        _write_usage_log(req_dir, entries)
        result = done_efficiency_aggregate(self.root, "req-99")
        rows = result["stage_role_rows"]
        executing_rows = [r for r in rows if r["stage"] == "executing"]
        self.assertEqual(len(executing_rows), 3, "同 stage 不同 role 应各出 1 行")


class SameStageRoleModelAccumTest(unittest.TestCase):
    """TC-05: 同 (stage, role, model) 多 entry 累加."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_accumulate_same_key(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        entries = [
            {"stage": "executing", "role": "executing", "model": "sonnet",
             "usage": {"total_tokens": 100, "tool_uses": 1}},
            {"stage": "executing", "role": "executing", "model": "sonnet",
             "usage": {"total_tokens": 200, "tool_uses": 2}},
            {"stage": "executing", "role": "executing", "model": "sonnet",
             "usage": {"total_tokens": 300, "tool_uses": 3}},
        ]
        _write_usage_log(req_dir, entries)
        result = done_efficiency_aggregate(self.root, "req-99")
        rows = result["stage_role_rows"]
        executing_rows = [r for r in rows if r["stage"] == "executing"]
        self.assertEqual(len(executing_rows), 1, "同 (stage, role, model) 应合并为 1 行")
        self.assertEqual(executing_rows[0]["total_tokens"], 600)
        self.assertEqual(executing_rows[0]["tool_uses"], 6)


class LegacySchemaCompatTest(unittest.TestCase):
    """TC-06: 历史 req 旧 schema 兼容（无 task_type 字段）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_legacy_no_task_type(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-40"
        req_dir.mkdir(parents=True, exist_ok=True)
        # Write entries without task_type (legacy format)
        content = """- ts: 2026-04-25T10:00:00+00:00
  stage: executing
  role: executing
  model: sonnet
  usage:
    input_tokens: 100
    output_tokens: 50
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 150
    tool_uses: 2
    duration_ms: 1000
"""
        (req_dir / "usage-log.yaml").write_text(content, encoding="utf-8")
        # Should not raise
        result = done_efficiency_aggregate(self.root, "req-40")
        rows = result["stage_role_rows"]
        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 1)


class DoneMdSingleTableTest(unittest.TestCase):
    """TC-07: done.md 模板含单表头（9 列）."""

    def test_done_md_has_single_table(self) -> None:
        done_md = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        content = done_md.read_text(encoding="utf-8")
        self.assertIn("各阶段切片", content, "done.md 应含单表段「各阶段切片」")
        self.assertIn("stage | role | model | input_tokens", content,
                      "单表应含 stage / role / model / input_tokens 列头")
        self.assertIn("tool_uses", content, "单表应含 tool_uses 列")
        # Old two-table headers should be gone
        self.assertNotIn("各阶段耗时分布", content, "旧「各阶段耗时分布」表应已删除")
        self.assertNotIn("各阶段 token 分布", content, "旧「各阶段 token 分布」表应已删除")


class ScaffoldMirrorTest(unittest.TestCase):
    """TC-08: scaffold mirror 同步（done.md）."""

    def test_done_md_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        mirror = (REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
                  / ".workflow" / "context" / "roles" / "done.md")
        self.assertEqual(
            source.read_text(encoding="utf-8"),
            mirror.read_text(encoding="utf-8"),
            "done.md scaffold mirror 应与源文件内容相同",
        )


if __name__ == "__main__":
    unittest.main()
