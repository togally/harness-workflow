"""Tests for req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-05（CLI 路径对齐扁平化）.

覆盖 create_regression 的新扁平路径行为：
- req-id >= 39：机器型文档落 .workflow/state/sessions/{req-id}/regressions/{reg-id}/，
  对人文档 placeholder 落 artifacts/ 扁平根（reg-NN-回归简报.md）。
- req-id <= 38：legacy 路径（req 目录下的 regressions/ 子目录）保持不变。
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
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{req_id}"',
            f'current_requirement_title: "{req_title}"',
            'stage: "executing"',
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
            'stage: "executing"',
            "",
        ]),
        encoding="utf-8",
    )
    return req_dir


class CreateRegressionFlatPathTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_regression_flat_path_for_new_req(self) -> None:
        """req-id >= 39: regression.md / analysis.md 落 .workflow/state/sessions/{req-id}/regressions/{reg-id}/.
        旧 artifacts/.../regressions/ 子目录不存在。"""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-39", "test req 39")
        rc = create_regression(self.root, "some regression issue")
        self.assertEqual(rc, 0)

        state_reg_base = self.root / ".workflow" / "state" / "sessions" / "req-39" / "regressions"
        reg_dirs = list(state_reg_base.glob("reg-*"))
        self.assertTrue(reg_dirs, "reg-* 目录必须在 state/sessions/req-39/regressions/ 下存在")
        reg_dir = reg_dirs[0]
        self.assertTrue((reg_dir / "regression.md").exists(), "regression.md 应在 state 目录下")
        self.assertTrue((reg_dir / "analysis.md").exists(), "analysis.md 应在 state 目录下")
        self.assertTrue((reg_dir / "decision.md").exists(), "decision.md 应在 state 目录下")
        self.assertTrue((reg_dir / "meta.yaml").exists(), "meta.yaml 应在 state 目录下")

    def test_create_regression_flat_no_old_regressions_dir(self) -> None:
        """req-id >= 39: artifacts/req-dir/regressions/ 子目录不应被创建。"""
        from harness_workflow.workflow_helpers import create_regression

        req_dir = _init_harness_repo(self.root, "req-40", "test req 40")
        create_regression(self.root, "some regression flat")

        regressions_legacy_dir = req_dir / "regressions"
        self.assertFalse(regressions_legacy_dir.exists(), "新扁平 req 不应在 artifacts/ 下建 regressions/ 目录")

    def test_create_regression_flat_placeholder_brief_in_artifacts(self) -> None:
        """req-id >= 39: 回归简报 placeholder 应平铺在 artifacts/ req 根目录."""
        from harness_workflow.workflow_helpers import create_regression

        req_dir = _init_harness_repo(self.root, "req-39", "test req 39")
        create_regression(self.root, "brief placeholder regression")

        brief_files = list(req_dir.glob("reg-*-回归简报.md"))
        self.assertTrue(brief_files, "reg-NN-回归简报.md placeholder 应平铺于 artifacts/ req 根目录")

    def test_create_regression_legacy_path_for_req_before_39(self) -> None:
        """req-id <= 38: regression.md 仍落 artifacts/.../regressions/{reg-id}-{slug}/（legacy 路径不变）."""
        from harness_workflow.workflow_helpers import create_regression

        req_dir = _init_harness_repo(self.root, "req-38", "test req 38 legacy")
        rc = create_regression(self.root, "legacy regression issue")
        self.assertEqual(rc, 0)

        regressions_dir = req_dir / "regressions"
        reg_dirs = list(regressions_dir.glob("reg-*"))
        self.assertTrue(reg_dirs, "legacy req 的 regression 应在 artifacts/regressions/ 子目录下")
        reg_dir = reg_dirs[0]
        self.assertTrue((reg_dir / "regression.md").exists(), "regression.md 应在 legacy regressions/ 目录下")

    def test_create_regression_legacy_no_state_sessions(self) -> None:
        """req-id <= 38: .workflow/state/sessions/ 下不应创建 regressions 目录（legacy 路径不走新分支）."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-37", "test req 37 legacy")
        create_regression(self.root, "legacy regression no state sessions")

        state_reg_base = self.root / ".workflow" / "state" / "sessions" / "req-37" / "regressions"
        self.assertFalse(state_reg_base.exists(), "legacy req 不应在 state/sessions/ 下创建 regressions 目录")


if __name__ == "__main__":
    unittest.main()
