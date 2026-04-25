"""Tests for chg-05 / req-41 Scope-效率字段：done 阶段交付总结 §效率与成本聚合逻辑。

覆盖：
- test_done_delivery_summary_efficiency_section：usage-log 有 ≥2 entries + ≥3 stage_timestamps，
  断言聚合结果四子字段全填、值可追溯。
- test_done_delivery_summary_empty_usage_log：usage-log 为空，四子字段标 ⚠️ 无数据。
- test_done_delivery_summary_field_order_fixed：done.md 模板字段顺序固定（总耗时 → 总 token
  → 各阶段耗时分布 → 各阶段 token 分布）。

AC: AC-11（模板扩展）/ AC-13 (d) 起点 / AC-15（mirror diff 归零）。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_req_dir(root: Path, req_id: str = "req-99", slug: str = "smoke") -> Path:
    """Build minimal .workflow/flow/requirements/{req-id}-{slug}/ directory."""
    req_dir = root / ".workflow" / "flow" / "requirements" / f"{req_id}-{slug}"
    req_dir.mkdir(parents=True, exist_ok=True)
    return req_dir


_USAGE_LOG_TWO_ENTRIES = """\
- ts: 2026-04-20T10:00:00+00:00
  stage: planning
  chg_id: chg-01
  role: analyst
  model: claude-opus-4-5
  usage:
    input_tokens: 1000
    output_tokens: 200
    cache_read_input_tokens: 50
    cache_creation_input_tokens: 10
    total_tokens: 1260
    tool_uses: 5
    duration_ms: 30000

- ts: 2026-04-20T11:00:00+00:00
  stage: executing
  chg_id: chg-02
  role: executing
  model: claude-sonnet-4-6
  usage:
    input_tokens: 800
    output_tokens: 300
    cache_read_input_tokens: 100
    cache_creation_input_tokens: 20
    total_tokens: 1220
    tool_uses: 8
    duration_ms: 45000
"""

_REQ_YAML_THREE_STAGES = """\
id: req-99
title: smoke test
stage: done
status: active
created_at: "2026-04-20"
started_at: "2026-04-20T09:00:00+00:00"
completed_at: null
stage_timestamps:
  requirement_review: "2026-04-20T09:00:00+00:00"
  planning: "2026-04-20T10:00:00+00:00"
  executing: "2026-04-20T11:00:00+00:00"
description: ""
"""


class TestDoneDeliverySummaryEfficiencySection(unittest.TestCase):
    """§效率与成本聚合：有数据时四子字段全填、值可追溯。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.req_dir = _build_req_dir(self.root)
        _write_yaml(self.req_dir / "usage-log.yaml", _USAGE_LOG_TWO_ENTRIES)
        _write_yaml(self.root / ".workflow" / "flow" / "requirements" / "req-99-smoke" / "req-99.yaml", _REQ_YAML_THREE_STAGES)

    def test_efficiency_section_all_fields_populated(self) -> None:
        """四子字段均非 ⚠️ 无数据，值与 mock 源可追溯。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")

        no_data = "⚠️ 无数据"

        # total_duration_s should be numeric (not NO_DATA)
        self.assertNotEqual(result["total_duration_s"], no_data, "total_duration_s should not be NO_DATA")
        self.assertNotEqual(result["total_duration_human"], no_data, "total_duration_human should not be NO_DATA")

        # total_tokens should be a dict
        self.assertIsInstance(result["total_tokens"], dict, "total_tokens should be a dict")
        tt = result["total_tokens"]
        # Verify sums: 1260 + 1220 = 2480
        self.assertEqual(tt["total"], 2480, f"total_tokens['total'] expected 2480, got {tt['total']}")
        self.assertEqual(tt["input"], 1800, f"total_tokens['input'] expected 1800")
        self.assertEqual(tt["output"], 500, f"total_tokens['output'] expected 500")

        # stage_durations: list with 3 rows matching mock
        self.assertIsInstance(result["stage_durations"], list, "stage_durations should be a list")
        stages = [row["stage"] for row in result["stage_durations"]]
        self.assertIn("requirement_review", stages)
        self.assertIn("planning", stages)
        self.assertIn("executing", stages)

        # role_tokens: list with 2 rows (analyst + executing)
        self.assertIsInstance(result["role_tokens"], list, "role_tokens should be a list")
        roles = {row["role"] for row in result["role_tokens"]}
        self.assertIn("analyst", roles)
        self.assertIn("executing", roles)

        # role_tokens sorted by total_tokens descending (analyst 1260 > executing 1220 — wait: sorted desc)
        totals = [row["total_tokens"] for row in result["role_tokens"]]
        self.assertEqual(totals, sorted(totals, reverse=True), "role_tokens should be sorted by total_tokens desc")

    def test_stage_durations_row_count_matches_mock(self) -> None:
        """stage_durations 行数 = mock stage_timestamps 条数。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")
        self.assertEqual(len(result["stage_durations"]), 3)

    def test_role_tokens_row_count_matches_entries(self) -> None:
        """role_tokens 行数 = mock distinct role×model 对数（2）。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")
        self.assertEqual(len(result["role_tokens"]), 2)

    def test_total_duration_s_is_positive_int(self) -> None:
        """total_duration_s 为正整数（从第一 stage 到最后 stage）。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")
        self.assertIsInstance(result["total_duration_s"], int)
        self.assertGreater(result["total_duration_s"], 0)  # type: ignore[operator]


class TestDoneDeliverySummaryEmptyUsageLog(unittest.TestCase):
    """§效率与成本聚合：usage-log 为空时四子字段标 ⚠️ 无数据。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.req_dir = _build_req_dir(self.root)

    def test_empty_usage_log_file(self) -> None:
        """usage-log.yaml 存在但内容为空 → 四子字段全标 ⚠️ 无数据。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        _write_yaml(self.req_dir / "usage-log.yaml", "")  # empty

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")

        no_data = "⚠️ 无数据"
        self.assertEqual(result["total_duration_s"], no_data)
        self.assertEqual(result["total_duration_human"], no_data)
        self.assertEqual(result["total_tokens"], no_data)
        self.assertEqual(result["stage_durations"], no_data)
        self.assertEqual(result["role_tokens"], no_data)

    def test_missing_usage_log_file(self) -> None:
        """usage-log.yaml 不存在 → 四子字段全标 ⚠️ 无数据。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")

        no_data = "⚠️ 无数据"
        self.assertEqual(result["total_duration_s"], no_data)
        self.assertEqual(result["total_tokens"], no_data)
        self.assertEqual(result["stage_durations"], no_data)
        self.assertEqual(result["role_tokens"], no_data)

    def test_empty_list_usage_log(self) -> None:
        """usage-log.yaml 含空列表 → 四子字段全标 ⚠️ 无数据。"""
        from harness_workflow.workflow_helpers import done_efficiency_aggregate

        _write_yaml(self.req_dir / "usage-log.yaml", "[]")

        result = done_efficiency_aggregate(self.root, "req-99", "smoke")

        no_data = "⚠️ 无数据"
        self.assertEqual(result["total_tokens"], no_data)
        self.assertEqual(result["stage_durations"], no_data)
        self.assertEqual(result["role_tokens"], no_data)


class TestDoneDeliverySummaryFieldOrderFixed(unittest.TestCase):
    """done.md 模板中 §效率与成本四子字段顺序固定（总耗时→总 token→各阶段耗时→各阶段 token）。"""

    DONE_MD = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"

    def test_efficiency_section_present(self) -> None:
        """done.md 含 ## 效率与成本 段。"""
        content = self.DONE_MD.read_text(encoding="utf-8")
        self.assertIn("## 效率与成本", content)

    def test_field_order_fixed(self) -> None:
        """四子字段按规定顺序出现：总耗时 → 总 token → 各阶段耗时分布 → 各阶段 token 分布。"""
        content = self.DONE_MD.read_text(encoding="utf-8")
        lines = content.splitlines()

        subfields = ["### 总耗时", "### 总 token", "### 各阶段耗时分布", "### 各阶段 token 分布"]
        positions = []
        for sf in subfields:
            for i, line in enumerate(lines):
                if line.strip() == sf:
                    positions.append(i)
                    break
            else:
                self.fail(f"Missing subfield in done.md: {sf}")

        self.assertEqual(
            positions,
            sorted(positions),
            f"Field order not ascending: {list(zip(subfields, positions))}",
        )

    def test_all_four_subfields_present(self) -> None:
        """四子字段全部存在于 done.md 中。"""
        content = self.DONE_MD.read_text(encoding="utf-8")
        for sf in ("### 总耗时", "### 总 token", "### 各阶段耗时分布", "### 各阶段 token 分布"):
            self.assertIn(sf, content, f"Missing: {sf}")

    def test_usage_log_and_stage_timestamps_mentioned(self) -> None:
        """done.md 含 usage-log.yaml 和 stage_timestamps 的聚合来源提及 ≥2 次。"""
        content = self.DONE_MD.read_text(encoding="utf-8")
        count_usage = content.count("usage-log.yaml")
        count_ts = content.count("stage_timestamps")
        self.assertGreaterEqual(count_usage + count_ts, 2, "usage-log.yaml + stage_timestamps mentions < 2")

    def test_no_data_marker_mentioned(self) -> None:
        """done.md 含"⚠️ 无数据"禁止编造标记。"""
        content = self.DONE_MD.read_text(encoding="utf-8")
        self.assertIn("⚠️ 无数据", content)

    def test_mirror_diff_zero(self) -> None:
        """scaffold_v2 mirror 与 done.md 完全一致（diff 归零）。"""
        mirror = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "done.md"
        self.assertTrue(mirror.exists(), f"Mirror not found: {mirror}")
        self.assertEqual(
            self.DONE_MD.read_text(encoding="utf-8"),
            mirror.read_text(encoding="utf-8"),
            "done.md and scaffold_v2 mirror are not identical",
        )


if __name__ == "__main__":
    unittest.main()
