"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖 req-39（state-flat）/ req-38（legacy）路径分支。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout
- req-38（原 legacy）/ req-39/40（原 state-flat）现在也走 flow layout
- _next_chg_id 扫 flow req_dir/changes/chg-* 分配 id（不再扫 state/sessions）

保留合规测试（无 changes/ 子目录等），更新预期路径为 flow layout。
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
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
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
            'stage: "analysis"',
            'operation_type: "requirement"',
            f'operation_target: "{current_req_id}"',
            'conversation_mode: "open"',
            'active_requirements: []',
            "",
        ]),
        encoding="utf-8",
    )


class CreateRequirementFlatPathTest(unittest.TestCase):
    """bugfix-11 方向C: 所有 req（含原 flat / legacy 区间）一律走 flow layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_requirement_flat_state_path(self) -> None:
        """req-40（原 state-flat 区间）: 方向C 后改走 flow layout，requirement.md 落 flow/requirements/."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        rc = create_requirement(self.root, None, requirement_id="req-40", title="flat req test")
        self.assertEqual(rc, 0)

        # 方向C：requirement.md 应在 flow/requirements，不在 state/requirements
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-40-*"))
        self.assertTrue(req_dirs, "方向C: flow/requirements/ 下应存在 req-40-* 目录")
        req_md = req_dirs[0] / "requirement.md"
        self.assertTrue(req_md.exists(), "方向C: requirement.md 应落在 flow 目录")

        # 原 state 路径不应被创建
        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-40"
        self.assertFalse(
            state_req_dir.exists(),
            "方向C: 不应在 state/requirements/req-40/ 下建子目录（已废弃 state-flat 路径）",
        )

    def test_create_requirement_flat_no_changes_subdir(self) -> None:
        """req-40: artifacts/ 目录不应建 changes/ 子目录（方向C 保持此约束）。"""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-40", title="flat req no changes")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-40-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-40-* 目录")
        changes_dir = req_dirs[0] / "changes"
        self.assertFalse(changes_dir.exists(), "req 不应在 artifacts/ 下建 changes/ 子目录")

    def test_create_requirement_flat_no_requirement_md_in_artifacts(self) -> None:
        """req-40: requirement.md 不应出现在 artifacts/ req 目录下（机器型文档落 flow/）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-40", title="flat req 40 test")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-40-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-40-* 目录")
        req_md_in_artifacts = req_dirs[0] / "requirement.md"
        self.assertFalse(
            req_md_in_artifacts.exists(),
            "requirement.md 不应落在 artifacts/ 目录下（机器型文档专属 flow/）",
        )

    def test_create_requirement_legacy_path(self) -> None:
        """req-38（原 legacy 区间）: 方向C 后改走 flow layout，requirement.md 落 flow/requirements/."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        rc = create_requirement(self.root, None, requirement_id="req-38", title="legacy req test")
        self.assertEqual(rc, 0)

        # 方向C：requirement.md 应在 flow/requirements，不在 legacy artifacts/
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-38-*"))
        self.assertTrue(req_dirs, "方向C: flow/requirements/ 下应存在 req-38-* 目录")
        req_md = req_dirs[0] / "requirement.md"
        self.assertTrue(
            req_md.exists(),
            "方向C: requirement.md 应落在 flow 路径，不在 legacy artifacts/",
        )

    def test_create_requirement_legacy_creates_changes_subdir(self) -> None:
        """req-37（原 legacy 区间）: 方向C 后不创建 artifacts/req-dir/changes/（废弃 legacy 分支）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_for_req(self.root)
        create_requirement(self.root, None, requirement_id="req-37", title="legacy req 37 test")

        # 方向C：artifacts/ 下不建 changes/ 子目录
        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-37-*"))
        # artifacts/ 下应有根目录（对人文档占位），但无 changes/ 子目录
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-37-* 目录（对人文档占位）")
        changes_dir = req_dirs[0] / "changes"
        self.assertFalse(
            changes_dir.exists(),
            "方向C: 不应在 artifacts/ 下建 changes/ 子目录（废弃 legacy 分支）",
        )


class NextChgIdFlatScanTest(unittest.TestCase):
    """bugfix-11 方向C: _next_chg_id 扫 flow req_dir/changes/chg-* 分配 id."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def _init_repo_with_existing_chgs(self, req_id: str, req_title: str, existing_chg_ids: list[str]) -> Path:
        """Create repo with pre-existing chg dirs in flow/requirements/{req-id}-{slug}/changes/."""
        _init_harness_repo_for_req(self.root)
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
        dir_name = f"{req_id}-{slug}"
        # flow req dir（方向C 的权威路径）
        flow_req_dir = self.root / ".workflow" / "flow" / "requirements" / dir_name
        flow_req_dir.mkdir(parents=True, exist_ok=True)
        # Create existing chg dirs in flow changes/
        for chg_id in existing_chg_ids:
            (flow_req_dir / "changes" / chg_id).mkdir(parents=True, exist_ok=True)
        return flow_req_dir

    def test_next_chg_id_three_existing_returns_chg_04(self) -> None:
        """flow/changes/chg-01 ~ chg-03 → 下一个应 chg-04."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02", "chg-03"],
        )
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-04", f"chg-01~03 已存在，下一个应为 chg-04，实际得到 {next_id}")

    def test_next_chg_id_six_existing_returns_chg_07(self) -> None:
        """flow/changes/chg-01 ~ chg-06 → 下一个应 chg-07."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02", "chg-03", "chg-04", "chg-05", "chg-06"],
        )
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-07", f"chg-01~06 已存在，下一个应为 chg-07，实际得到 {next_id}")

    def test_next_chg_id_no_existing_returns_chg_01(self) -> None:
        """flow/changes/ 为空 → 下一个应 chg-01."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs("req-40", "test req 99", [])
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-01", f"无既有 chg，下一个应为 chg-01，实际得到 {next_id}")

    def test_next_chg_id_scans_state_not_artifacts_changes(self) -> None:
        """方向C: _next_chg_id 扫 flow req_dir/changes/（不再扫 state/sessions）."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = self._init_repo_with_existing_chgs(
            "req-40", "test req 99",
            ["chg-01", "chg-02"],
        )
        # flow changes 有 chg-01/02，应返回 chg-03
        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-40")
        self.assertEqual(next_id, "chg-03", f"flow changes 有 chg-01~02，下一个应为 chg-03，实际得到 {next_id}")


if __name__ == "__main__":
    unittest.main()
