"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖 req-39/40（flat）和 req-37/38（legacy）路径分支。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout
- create_change 始终在 .workflow/flow/requirements/{req-id}-{slug}/changes/{chg-id}-{slug}/ 落 change.md
- _next_chg_id 扫 flow req_dir/changes/chg-* 分配 id
- _use_flat_layout 已删除

保留布局合规测试，更新预期路径为 flow layout。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo(root: Path, req_id: str, req_title: str = "test req") -> Path:
    """Create minimal harness repo structure with an existing requirement in flow layout."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Build artifacts req dir (对人文档占位)
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
    # Build flow req dir (机器型文档根，方向C)
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{req_id}"',
            f'current_requirement_title: "{req_title}"',
            'stage: "planning"',
            'operation_type: "requirement"',
            f'operation_target: "{req_id}"',
            'conversation_mode: "open"',
            'active_requirements: []',
            "",
        ]),
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml").write_text(
        "\n".join([
            f'id: "{req_id}"',
            f'title: "{req_title}"',
            'stage: "planning"',
            "",
        ]),
        encoding="utf-8",
    )
    return flow_req_dir


class CreateChangeFlatPathTest(unittest.TestCase):
    """bugfix-11 方向C: 所有 req（含原 flat / legacy 区间）一律走 flow layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_change_flat_path_for_new_req(self) -> None:
        """方向C: req-39 的 change.md / plan.md 落 flow/requirements/{req-id}-{slug}/changes/{chg-id}/."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-39", "test req 39")
        rc = create_change(self.root, "my change flat")
        self.assertEqual(rc, 0)

        # 方向C: 机器型文档落 flow/requirements/req-39-*/changes/
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-39-*"))
        self.assertTrue(req_dirs, "flow/requirements/ 下应存在 req-39-* 目录")
        chg_dirs = list((req_dirs[0] / "changes").glob("chg-*"))
        self.assertTrue(chg_dirs, "chg-* 目录必须在 flow/requirements/req-39-*/changes/ 下存在")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 flow changes 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 flow changes 目录下")
        self.assertTrue((chg_dir / "session-memory.md").exists(), "session-memory.md 应在 flow changes 目录下")

    def test_create_change_flat_no_old_changes_dir(self) -> None:
        """方向C: artifacts/req-dir/changes/ 子目录不应被创建（机器型文档不落 artifacts）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-40", "test req 40")
        create_change(self.root, "some change new flat")

        # 验证对人 artifacts 目录下无 changes/
        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("test req 40") or "test-req-40"
        artifacts_req_dir = self.root / "artifacts" / "main" / "requirements" / f"req-40-{slug}"
        changes_legacy_dir = artifacts_req_dir / "changes"
        self.assertFalse(changes_legacy_dir.exists(), "方向C: artifacts/ 下不应建 changes/ 目录（机器型文档落 flow）")

    def test_create_change_flat_placeholder_brief_in_artifacts(self) -> None:
        """方向C: artifacts/ req 根目录下不应创建 变更简报.md placeholder（废弃四类 brief）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-39", "test req 39")
        create_change(self.root, "brief placeholder test")

        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("test req 39") or "test-req-39"
        req_dir = self.root / "artifacts" / "main" / "requirements" / f"req-39-{slug}"
        # 方向C（废弃四类 brief）：不应在 artifacts/ 下创建 变更简报.md placeholder
        brief_files = list(req_dir.glob("chg-*-变更简报.md"))
        self.assertFalse(brief_files, "方向C: 不应在 artifacts/ 下创建 变更简报.md placeholder（废弃四类 brief）")

    def test_create_change_legacy_path_for_req_before_39(self) -> None:
        """方向C: req-38（原 legacy 区间）也走 flow layout，change.md 落 flow/requirements/req-38-*/changes/."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-38", "test req 38 legacy")
        rc = create_change(self.root, "legacy change test")
        self.assertEqual(rc, 0)

        # 方向C: change 应在 flow/requirements/req-38-*/changes/ 下（不在 artifacts/changes/）
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-38-*"))
        self.assertTrue(req_dirs, "flow/requirements/ 下应存在 req-38-* 目录")
        chg_dirs = list((req_dirs[0] / "changes").glob("chg-*"))
        self.assertTrue(chg_dirs, "方向C: req-38 change 应在 flow/requirements/req-38-*/changes/ 下")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 flow changes 目录下")

    def test_create_change_legacy_no_state_sessions(self) -> None:
        """方向C: req-37（原 legacy 区间）的 change 不应创建 state/sessions/ 目录（废弃 state-flat 分支）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-37", "test req 37 legacy")
        create_change(self.root, "legacy chg no state sessions")

        # 方向C: 不应在 state/sessions/ 下创建 chg 目录
        state_sessions = self.root / ".workflow" / "state" / "sessions" / "req-37"
        self.assertFalse(state_sessions.exists(), "方向C: 不应在 state/sessions/ 下创建 chg 目录（废弃 state-flat 分支）")

    def test_next_chg_id_scans_state_sessions_for_new_req(self) -> None:
        """方向C: _next_chg_id 扫 flow req_dir/changes/chg-* 分配 id（不扫 state/sessions）."""
        from harness_workflow.workflow_helpers import _next_chg_id

        flow_req_dir = _init_harness_repo(self.root, "req-39", "test req 39")
        # 预先在 flow req changes/ 建一个 chg-01 目录，验证 _next_chg_id 从 02 开始
        existing_chg = flow_req_dir / "changes" / "chg-01-existing"
        existing_chg.mkdir(parents=True)

        next_id = _next_chg_id(flow_req_dir, root=self.root, req_id="req-39")
        self.assertEqual(next_id, "chg-02", f"下一个 chg id 应为 chg-02，实际得到 {next_id}")

    def test_legacy_helpers_all_deleted(self) -> None:
        """方向C: _use_flat_layout 和 _use_flow_layout 函数均已删除。"""
        import harness_workflow.workflow_helpers as wh

        # 确认 _use_flat_layout 已被删除（方向C 约束）
        self.assertFalse(
            hasattr(wh, "_use_flat_layout"),
            "方向C: _use_flat_layout 已废弃并删除，不应存在",
        )
        # 确认 _use_flow_layout 也已被删除（bugfix-11 round-2 修正）
        self.assertFalse(
            hasattr(wh, "_use_flow_layout"),
            "方向C: _use_flow_layout 已废弃并删除，不应存在",
        )


if __name__ == "__main__":
    unittest.main()
