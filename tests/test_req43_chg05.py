"""Tests for req-43（交付总结完善）/ chg-05（sug 直接处理路径产出 3 段轻量交付总结 + State 校验扩三类任务）.

- TC-01: _create_sug_delivery_summary 产出 3 段轻量交付总结
- TC-02: archive_suggestion 触发产出 sug 交付总结
- TC-03: sug → req 转化路径不重复产出（不调 _create_sug_delivery_summary）
- TC-04: _collect_suggestion_items 检出缺失
- TC-05: base-role.md State 层校验含三类任务说明
- TC-06: repository-layout.md 含 sug 子树落位
- TC-07: done.md 含三类任务 usage-log 说明
- TC-08: scaffold mirror 同步（base-role.md + done.md + repository-layout.md）
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_repo(root: Path) -> None:
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    # Need context dir for ensure_harness_root
    (root / ".workflow" / "context").mkdir(parents=True)
    # Write a minimal runtime.yaml
    runtime_path = root / ".workflow" / "state" / "runtime.yaml"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_text("current_requirement: req-43\nstage: executing\n", encoding="utf-8")


class CreateSugDeliverySummaryTest(unittest.TestCase):
    """TC-01: _create_sug_delivery_summary 产出 3 段轻量 交付总结.md."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_creates_delivery_summary(self) -> None:
        from harness_workflow.workflow_helpers import _create_sug_delivery_summary
        _create_sug_delivery_summary(
            self.root,
            sug_id="sug-30",
            slug="test-suggestion",
            title="Test Suggestion",
            action="archived",
            body="This is the suggestion body.",
            current_branch="main",
        )
        summary_path = (self.root / "artifacts" / "main" / "suggestions"
                        / "sug-30-test-suggestion" / "交付总结.md")
        self.assertTrue(summary_path.exists(), "交付总结.md 应被创建")
        content = summary_path.read_text(encoding="utf-8")
        self.assertIn("建议是什么", content, "应含「建议是什么」段")
        self.assertIn("处理结果", content, "应含「处理结果」段")
        self.assertIn("后续", content, "应含「后续」段")
        self.assertIn("sug-30", content, "应含 sug_id")


class ArchiveSuggestionCreatesDeliveryTest(unittest.TestCase):
    """TC-02: archive_suggestion 触发产出 sug 交付总结."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_archive_creates_delivery_summary(self) -> None:
        from harness_workflow.workflow_helpers import archive_suggestion
        # Create a sug file in applied state
        sug_path = self.root / ".workflow" / "flow" / "suggestions" / "sug-30-test.md"
        sug_path.write_text(
            '---\nid: sug-30\ntitle: "Test"\nstatus: applied\ncreated_at: 2026-04-25\npriority: medium\n---\n\nTest suggestion body.\n',
            encoding="utf-8",
        )
        archive_suggestion(self.root, "sug-30")
        # Check that delivery summary was created
        sug_dirs = list((self.root / "artifacts").rglob("交付总结.md"))
        self.assertGreater(len(sug_dirs), 0, "archive_suggestion 应触发产出交付总结.md")


class SugReqConvertNoDeliveryTest(unittest.TestCase):
    """TC-03: sug → req 转化路径（apply_suggestion 调 create_requirement）不产出 sug 子树交付总结."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_no_duplicate_delivery_for_converted_sug(self) -> None:
        # apply_suggestion creates a requirement (sug → req), so no sug 交付总结 should appear
        # We test this by verifying _create_sug_delivery_summary is not called in apply_suggestion
        # Since apply_suggestion calls create_requirement and moves sug to archive/,
        # we check that the sug sub-tree in artifacts/ is NOT created
        from harness_workflow.workflow_helpers import _create_sug_delivery_summary
        # Manually verify that apply_suggestion code path doesn't call _create_sug_delivery_summary
        import inspect
        source = inspect.getsource(
            __import__('harness_workflow.workflow_helpers', fromlist=['apply_suggestion']).apply_suggestion
        )
        self.assertNotIn("_create_sug_delivery_summary", source,
                         "apply_suggestion（sug → req 转化）不应调 _create_sug_delivery_summary")


class CollectSuggestionItemsMissingTest(unittest.TestCase):
    """TC-04: _collect_suggestion_items 检出交付总结缺失."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_repo(self.root)

    def test_missing_sug_delivery_summary_detected(self) -> None:
        from harness_workflow.validate_human_docs import _collect_suggestion_items, STATUS_MISSING
        sug_dir = self.root / "artifacts" / "main" / "suggestions" / "sug-30-test"
        sug_dir.mkdir(parents=True, exist_ok=True)
        # No 交付总结.md created
        items = _collect_suggestion_items(sug_dir)
        missing = [i for i in items if i.status == STATUS_MISSING]
        self.assertTrue(len(missing) > 0, "缺失的 sug 交付总结.md 应被检出")
        filenames = [i.filename for i in missing]
        self.assertIn("交付总结.md", filenames)


class BaseRoleStateLayerThreeTypesTest(unittest.TestCase):
    """TC-05: base-role.md State 层校验含三类任务说明."""

    def test_base_role_has_three_task_types(self) -> None:
        base_role = REPO_ROOT / ".workflow" / "context" / "roles" / "base-role.md"
        content = base_role.read_text(encoding="utf-8")
        self.assertIn("三类任务", content, "base-role.md State 层应提到三类任务")
        self.assertIn("task_type", content, "base-role.md State 层应含 task_type 字段说明")


class RepoLayoutSugSubtreeTest(unittest.TestCase):
    """TC-06: repository-layout.md 含 sug 子树落位."""

    def test_repo_layout_has_sug_subtree(self) -> None:
        layout = REPO_ROOT / ".workflow" / "flow" / "repository-layout.md"
        content = layout.read_text(encoding="utf-8")
        self.assertIn("suggestions/", content, "repository-layout.md 应含 suggestions/ 子树定义")
        self.assertIn("sug 交付总结", content, "repository-layout.md §2 白名单应含 sug 交付总结行")


class DoneMdThreeTypesTest(unittest.TestCase):
    """TC-07: done.md 含三类任务 usage-log 说明."""

    def test_done_md_has_three_types_mention(self) -> None:
        done_md = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        content = done_md.read_text(encoding="utf-8")
        self.assertIn("三类任务", content, "done.md 应含三类任务说明")


class ScaffoldMirrorTest(unittest.TestCase):
    """TC-08: scaffold mirror 同步（base-role.md + done.md + repository-layout.md）."""

    def test_base_role_mirror_sync(self) -> None:
        source = REPO_ROOT / ".workflow" / "context" / "roles" / "base-role.md"
        mirror = (REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
                  / ".workflow" / "context" / "roles" / "base-role.md")
        self.assertEqual(source.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"))

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
