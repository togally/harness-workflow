"""Tests for req-43（交付总结完善）/ chg-04（bugfix 引入 bugfix-交付总结.md（done 模板精简版））.

- TC-01: done_efficiency_aggregate task_type="bugfix" 路径切换
- TC-02: done_efficiency_aggregate task_type="req" 向后兼容
- TC-03: BUGFIX_LEVEL_DOCS 含 bugfix-交付总结.md
- TC-04: validate_human_docs 检出 bugfix-交付总结.md 缺失
- TC-05: done.md 含 bugfix 交付总结模板（修复验证段）
- TC-06: done.md 模板无 chg 段（精简验证）
- TC-07: stage_role_rows bugfix 路径正确读取
- TC-08: scaffold mirror 同步（done.md + repository-layout.md）
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


def _write_bugfix_usage_log(root: Path, bugfix_id: str) -> None:
    session_dir = root / ".workflow" / "state" / "sessions" / bugfix_id
    session_dir.mkdir(parents=True, exist_ok=True)
    content = """- ts: 2026-04-25T10:00:00+00:00
  task_type: bugfix
  stage: executing
  role: executing
  model: sonnet
  usage:
    input_tokens: 200
    output_tokens: 80
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 280
    tool_uses: 3
    duration_ms: 2000
- ts: 2026-04-25T11:00:00+00:00
  task_type: bugfix
  stage: testing
  role: testing
  model: sonnet
  usage:
    input_tokens: 100
    output_tokens: 40
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 140
    tool_uses: 2
    duration_ms: 1500
"""
    (session_dir / "usage-log.yaml").write_text(content, encoding="utf-8")


class BugfixHelperPathTest(unittest.TestCase):
    """TC-01: done_efficiency_aggregate task_type="bugfix" 路径切换."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_bugfix_path_reads_sessions(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        _write_bugfix_usage_log(self.root, "bugfix-99")
        result = done_efficiency_aggregate(self.root, "bugfix-99", task_type="bugfix")
        rows = result["stage_role_rows"]
        self.assertIsInstance(rows, list)
        self.assertGreater(len(rows), 0, "bugfix task_type 路径应能读取到 entries")
        stages = [r["stage"] for r in rows]
        self.assertIn("executing", stages)
        self.assertIn("testing", stages)


class ReqHelperCompatTest(unittest.TestCase):
    """TC-02: done_efficiency_aggregate task_type="req" 向后兼容（不传 task_type 默认 req）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_default_task_type_req(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate, _NO_DATA
        # No usage-log for req-99
        req_dir = self.root / ".workflow" / "flow" / "requirements" / "req-99"
        req_dir.mkdir(parents=True, exist_ok=True)
        # Should not raise, returns _NO_DATA
        result = done_efficiency_aggregate(self.root, "req-99")
        self.assertEqual(result["stage_role_rows"], _NO_DATA)


class BugfixLevelDocsTest(unittest.TestCase):
    """TC-03: BUGFIX_LEVEL_DOCS 含 bugfix-交付总结.md."""

    def test_bugfix_level_docs_has_delivery_summary(self) -> None:
        from harness_workflow.validate_human_docs import BUGFIX_LEVEL_DOCS
        filenames = [doc[1] for doc in BUGFIX_LEVEL_DOCS]
        self.assertIn("bugfix-交付总结.md", filenames, "BUGFIX_LEVEL_DOCS 应含 bugfix-交付总结.md")


class ValidateHumanDocsBugfixMissingTest(unittest.TestCase):
    """TC-04: validate_human_docs 检出 bugfix-交付总结.md 缺失."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        # Create bugfix directory structure
        bugfix_dir = self.root / "artifacts" / "main" / "bugfixes" / "bugfix-99-test"
        bugfix_dir.mkdir(parents=True, exist_ok=True)
        # Don't create bugfix-交付总结.md

    def test_missing_bugfix_delivery_summary_detected(self) -> None:
        from harness_workflow.validate_human_docs import _collect_bugfix_items, STATUS_MISSING
        bugfix_dir = self.root / "artifacts" / "main" / "bugfixes" / "bugfix-99-test"
        items = _collect_bugfix_items(bugfix_dir)
        missing_filenames = [i.filename for i in items if i.status == STATUS_MISSING]
        self.assertIn("bugfix-交付总结.md", missing_filenames,
                      "validate_human_docs 应检出 bugfix-交付总结.md 缺失")


class DoneMdBugfixTemplateTest(unittest.TestCase):
    """TC-05: done.md 含 bugfix 交付总结模板（修复验证段）."""

    def test_done_md_has_bugfix_template(self) -> None:
        done_md = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        content = done_md.read_text(encoding="utf-8")
        self.assertIn("bugfix 交付总结模板", content, "done.md 应含 bugfix 交付总结模板段")
        self.assertIn("修复验证", content, "done.md bugfix 模板应含「修复验证」合并段")


class DoneMdNoChgSectionTest(unittest.TestCase):
    """TC-06: done.md bugfix 模板无 chg 段（精简验证）."""

    def test_done_md_bugfix_no_chg_section(self) -> None:
        done_md = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        content = done_md.read_text(encoding="utf-8")
        # The bugfix template should have "修复了什么" but not "## 交付了什么"
        # (which is in req template and includes chg listing)
        # Check bugfix template section
        bugfix_start = content.find("bugfix 交付总结模板（精简版）")
        if bugfix_start == -1:
            self.fail("done.md 应含 bugfix 交付总结模板段")
        bugfix_section = content[bugfix_start:]
        self.assertIn("修复了什么", bugfix_section, "bugfix 模板应含「修复了什么」段")
        self.assertNotIn("chg-NN", bugfix_section, "bugfix 精简模板不应含 chg 列举段")


class StageRoleRowsBugfixTest(unittest.TestCase):
    """TC-07: stage_role_rows bugfix 路径包含 regression/executing/testing/acceptance."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_bugfix_stage_role_rows(self) -> None:
        from harness_workflow.workflow_helpers import done_efficiency_aggregate
        session_dir = self.root / ".workflow" / "state" / "sessions" / "bugfix-99"
        session_dir.mkdir(parents=True, exist_ok=True)
        content = """- ts: 2026-04-25T09:00:00+00:00
  task_type: bugfix
  stage: regression
  role: regression
  model: opus
  usage:
    input_tokens: 300
    output_tokens: 100
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 400
    tool_uses: 4
    duration_ms: 3000
- ts: 2026-04-25T10:00:00+00:00
  task_type: bugfix
  stage: executing
  role: executing
  model: sonnet
  usage:
    input_tokens: 200
    output_tokens: 80
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 280
    tool_uses: 3
    duration_ms: 2000
- ts: 2026-04-25T11:00:00+00:00
  task_type: bugfix
  stage: acceptance
  role: acceptance
  model: sonnet
  usage:
    input_tokens: 100
    output_tokens: 40
    cache_read_input_tokens: 0
    cache_creation_input_tokens: 0
    total_tokens: 140
    tool_uses: 1
    duration_ms: 1000
"""
        (session_dir / "usage-log.yaml").write_text(content, encoding="utf-8")
        result = done_efficiency_aggregate(self.root, "bugfix-99", task_type="bugfix")
        rows = result["stage_role_rows"]
        stages = [r["stage"] for r in rows]
        self.assertIn("regression", stages)
        self.assertIn("executing", stages)
        self.assertIn("acceptance", stages)


class ScaffoldMirrorTest(unittest.TestCase):
    """TC-08: scaffold mirror 同步（done.md + repository-layout.md）."""

    def test_done_md_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        mirror = (REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
                  / ".workflow" / "context" / "roles" / "done.md")
        self.assertEqual(source.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"))

    def test_repository_layout_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "flow" / "repository-layout.md"
        mirror = (REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
                  / ".workflow" / "flow" / "repository-layout.md")
        self.assertEqual(source.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
