"""Tests for req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-05（CLI 路径对齐扁平化）.

覆盖 create_change / _next_chg_id 的新扁平路径行为：
- req-id >= 39：机器型文档落 .workflow/state/sessions/{req-id}/{chg-id}/，对人文档 placeholder 落 artifacts/ 扁平根。
- req-id <= 38：legacy 路径（changes/ 子目录）保持不变。
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
    """Create minimal harness repo structure with an existing requirement."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Build artifacts req dir
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
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
    return req_dir


class CreateChangeFlatPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_change_flat_path_for_new_req(self) -> None:
        """req-id >= 39: change.md / plan.md 落 .workflow/state/sessions/{req-id}/chg-01-{slug}/.
        旧 artifacts/changes/ 子目录不存在。"""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-39", "test req 39")
        rc = create_change(self.root, "my change flat")
        self.assertEqual(rc, 0)

        # 机器型文档落 state/sessions
        state_chg_dir = self.root / ".workflow" / "state" / "sessions" / "req-39"
        chg_dirs = list(state_chg_dir.glob("chg-*"))
        self.assertTrue(chg_dirs, "chg-* 目录必须在 state/sessions/req-39/ 下存在")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 state 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 state 目录下")
        self.assertTrue((chg_dir / "session-memory.md").exists(), "session-memory.md 应在 state 目录下")

    def test_create_change_flat_no_old_changes_dir(self) -> None:
        """req-id >= 39: artifacts/req-dir/changes/ 子目录不应被创建。"""
        from harness_workflow.workflow_helpers import create_change

        req_dir = _init_harness_repo(self.root, "req-40", "test req 40")
        create_change(self.root, "some change new flat")

        changes_legacy_dir = req_dir / "changes"
        self.assertFalse(changes_legacy_dir.exists(), "新扁平 req 不应在 artifacts/ 下建 changes/ 目录")

    def test_create_change_flat_placeholder_brief_in_artifacts(self) -> None:
        """req-id >= 39: 变更简报 placeholder 应平铺在 artifacts/ req 根目录."""
        from harness_workflow.workflow_helpers import create_change

        req_dir = _init_harness_repo(self.root, "req-39", "test req 39")
        create_change(self.root, "brief placeholder test")

        brief_files = list(req_dir.glob("chg-*-变更简报.md"))
        self.assertTrue(brief_files, "chg-NN-变更简报.md placeholder 应平铺于 artifacts/ req 根目录")

    def test_create_change_legacy_path_for_req_before_39(self) -> None:
        """req-id <= 38: change.md / plan.md 仍落 artifacts/.../changes/{chg-id}-{slug}/（legacy 路径不变）."""
        from harness_workflow.workflow_helpers import create_change

        req_dir = _init_harness_repo(self.root, "req-38", "test req 38 legacy")
        rc = create_change(self.root, "legacy change test")
        self.assertEqual(rc, 0)

        changes_dir = req_dir / "changes"
        chg_dirs = list(changes_dir.glob("chg-*"))
        self.assertTrue(chg_dirs, "legacy req 的 change 应在 artifacts/changes/ 子目录下")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 legacy changes/ 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 legacy changes/ 目录下")

    def test_create_change_legacy_no_state_sessions(self) -> None:
        """req-id <= 38: .workflow/state/sessions/ 下不应创建 chg 目录（legacy 路径不走新分支）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo(self.root, "req-37", "test req 37 legacy")
        create_change(self.root, "legacy chg no state sessions")

        state_sessions = self.root / ".workflow" / "state" / "sessions" / "req-37"
        self.assertFalse(state_sessions.exists(), "legacy req 不应在 state/sessions/ 下创建 chg 目录")

    def test_next_chg_id_scans_state_sessions_for_new_req(self) -> None:
        """req-id >= 39: _next_chg_id 应扫 state/sessions/{req-id}/chg-* 分配 id."""
        from harness_workflow.workflow_helpers import _next_chg_id

        req_dir = _init_harness_repo(self.root, "req-39", "test req 39")
        # 预先在 state/sessions/ 建一个 chg-01 目录，验证 _next_chg_id 从 02 开始
        existing_chg = self.root / ".workflow" / "state" / "sessions" / "req-39" / "chg-01-existing"
        existing_chg.mkdir(parents=True)

        next_id = _next_chg_id(req_dir, root=self.root, req_id="req-39")
        self.assertEqual(next_id, "chg-02", f"下一个 chg id 应为 chg-02，实际得到 {next_id}")

    def test_use_flat_layout_boundary(self) -> None:
        """_use_flat_layout: req-38 → False（legacy），req-39 → True（flat），req-40 → True（flat）."""
        from harness_workflow.workflow_helpers import _use_flat_layout

        self.assertFalse(_use_flat_layout("req-38"), "req-38 应走 legacy 路径（混合过渡期）")
        self.assertFalse(_use_flat_layout("req-37"), "req-37 应走 legacy 路径")
        self.assertTrue(_use_flat_layout("req-39"), "req-39 应走 flat 路径")
        self.assertTrue(_use_flat_layout("req-40"), "req-40 应走 flat 路径")
        self.assertFalse(_use_flat_layout(""), "空 id 应走 legacy 路径")
        self.assertFalse(_use_flat_layout("bugfix-01"), "bugfix id 不走 flat 路径")


if __name__ == "__main__":
    unittest.main()
