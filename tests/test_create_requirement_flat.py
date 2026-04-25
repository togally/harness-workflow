"""Tests for req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-07（create_requirement CLI 路径对齐补齐）.

覆盖 create_requirement / _next_chg_id 的新扁平路径行为：
- req-id >= 39：requirement.md 落 .workflow/state/requirements/{req-id}/requirement.md
  artifacts/ 目录只建根目录，不建 changes/ 子目录（扁平结构约束）
- req-id < 39：legacy 路径（artifacts/req-dir/requirement.md + changes/ 子目录）保持不变
- _next_chg_id 在 req-id >= 39 时扫 state/sessions/{req-id}/chg-* 分配 id
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo_for_req(root: Path, current_req_id: str = "") -> None:
    """Create minimal harness repo structure for create_requirement tests."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "archive").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{current_req_id}"',
            'current_requirement_title: ""',
            'stage: "requirement_review"',
            'operation_type: "requirement"',
            f'operation_target: "{current_req_id}"',
            'conversation_mode: "open"',
            'active_requirements: []',
            "",
        ]),
        encoding="utf-8",
    )


class CreateRequirementFlatPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_requirement_flat_state_path(self) -> None:
        """req-id >= 39: requirement.md 落 .workflow/state/requirements/{req-id}/requirement.md."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        rc = create_requirement(self.root, None, requirement_id="req-40", title="flat req test")
        self.assertEqual(rc, 0)

        state_req_file = self.root / ".workflow" / "state" / "requirements" / "req-40" / "requirement.md"
        self.assertTrue(
            state_req_file.exists(),
            f"requirement.md 应落在 state 目录 {state_req_file}，实际不存在",
        )

    def test_create_requirement_flat_no_changes_subdir(self) -> None:
        """req-id >= 39: artifacts/ 目录不应建 changes/ 子目录。"""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-40", title="flat req no changes")

        # Find the artifacts req dir
        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-40-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-40-* 目录")
        changes_dir = req_dirs[0] / "changes"
        self.assertFalse(
            changes_dir.exists(),
            "新扁平 req 不应在 artifacts/ 下建 changes/ 子目录",
        )

    def test_create_requirement_flat_no_requirement_md_in_artifacts(self) -> None:
        """req-id >= 39: requirement.md 不应出现在 artifacts/ req 目录下（机器型文档只落 state/）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-40", title="flat req 40 test")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-40-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-40-* 目录")
        req_md_in_artifacts = req_dirs[0] / "requirement.md"
        self.assertFalse(
            req_md_in_artifacts.exists(),
            "requirement.md 不应落在 artifacts/ 目录下（机器型文档专属 state/）",
        )

    def test_create_requirement_legacy_path(self) -> None:
        """req-id < 39: requirement.md 落 artifacts/req-dir/requirement.md（legacy 路径不变）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        rc = create_requirement(self.root, None, requirement_id="req-38", title="legacy req test")
        self.assertEqual(rc, 0)

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-38-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-38-* 目录")
        req_md_in_artifacts = req_dirs[0] / "requirement.md"
        self.assertTrue(
            req_md_in_artifacts.exists(),
            "legacy req 的 requirement.md 应在 artifacts/ req 目录下",
        )

    def test_create_requirement_legacy_creates_changes_subdir(self) -> None:
        """req-id < 39: legacy req 应建 artifacts/req-dir/changes/ 子目录。"""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-37", title="legacy req 37 test")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-37-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-37-* 目录")
        changes_dir = req_dirs[0] / "changes"
        self.assertTrue(
            changes_dir.exists(),
            "legacy req 应在 artifacts/ 下建 changes/ 子目录",
        )

    def test_create_requirement_legacy_no_state_req_dir(self) -> None:
        """req-id < 39: state/requirements/{req-id}/ 目录不应创建（仅 state yaml 存在）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-36", title="legacy req 36 test")

        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-36"
        self.assertFalse(
            state_req_dir.exists(),
            "legacy req 不应在 state/requirements/ 下建 req-id 子目录",
        )


class NextChgIdFlatScanTest(unittest.TestCase):
    """req-id >= 39: _next_chg_id 扫 state/sessions/{req-id}/chg-* 分配 id（fixture 覆盖）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def _init_repo_with_existing_chgs(self, req_id: str, req_title: str, existing_chg_ids: list[str]) -> Path:
        """Create repo with pre-existing chg dirs in state/sessions/{req-id}/."""
        _init_harness_repo_for_req(self.root)
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
        dir_name = f"{req_id}-{slug}"
        req_dir = self.root / "artifacts" / "main" / "requirements" / dir_name
        req_dir.mkdir(parents=True, exist_ok=True)
        # Create existing chg dirs in state/sessions
        state_sessions = self.root / ".workflow" / "state" / "sessions" / req_id
        for chg_id in existing_chg_ids:
            (state_sessions / chg_id).mkdir(parents=True, exist_ok=True)
        return req_dir

    def test_next_chg_id_three_existing_returns_chg_04(self) -> None:
        """fixture: state/sessions/req-40/chg-01 ~ chg-03 → 下一个应 chg-04."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02", "chg-03"],
        )
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-04", f"chg-01~03 已存在，下一个应为 chg-04，实际得到 {next_id}")

    def test_next_chg_id_six_existing_returns_chg_07(self) -> None:
        """fixture: state/sessions/req-40/chg-01 ~ chg-06 → 下一个应 chg-07."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02", "chg-03", "chg-04", "chg-05", "chg-06"],
        )
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-07", f"chg-01~06 已存在，下一个应为 chg-07，实际得到 {next_id}")

    def test_next_chg_id_no_existing_returns_chg_01(self) -> None:
        """fixture: state/sessions/req-40/ 为空 → 下一个应 chg-01."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs("req-40", "test req 99", [])
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-01", f"无既有 chg，下一个应为 chg-01，实际得到 {next_id}")

    def test_next_chg_id_scans_state_not_artifacts_changes(self) -> None:
        """req-id >= 39: _next_chg_id 以 state/sessions 为准，artifacts/changes/ 不影响计数（legacy fallback）."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02"],
        )
        # 即使 artifacts/changes/ 为空，也应从 state/sessions 扫到 chg-02 → 返回 chg-03
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-03", f"state 扫到 chg-02，下一个应为 chg-03，实际得到 {next_id}")


if __name__ == "__main__":
    unittest.main()
