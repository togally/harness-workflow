"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖 req-39/40（flat）和 req-37/38（legacy）路径分支。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout
- create_regression 始终在 .workflow/flow/requirements/{req-id}-{slug}/regressions/{reg-id}-{slug}/ 落文档
- req-37/38（原 legacy）也走 flow layout

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
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    req_dir.mkdir(parents=True)
    # flow req dir (机器型文档根，方向C)
    flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
    flow_req_dir.mkdir(parents=True)
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
    return flow_req_dir


class CreateRegressionFlatPathTest(unittest.TestCase):
    """bugfix-11 方向C: 所有 req（含原 flat / legacy 区间）一律走 flow layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_regression_flat_path_for_new_req(self) -> None:
        """方向C: req-39 regression 落 flow/requirements/req-39-*/regressions/reg-NN/."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-39", "test req 39")
        rc = create_regression(self.root, "some regression issue")
        self.assertEqual(rc, 0)

        # 方向C: regression 在 flow/requirements/req-39-*/regressions/
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-39-*"))
        self.assertTrue(req_dirs, "flow/requirements/ 下应存在 req-39-* 目录")
        reg_dirs = list((req_dirs[0] / "regressions").glob("reg-*"))
        self.assertTrue(reg_dirs, "reg-* 目录必须在 flow/requirements/req-39-*/regressions/ 下存在")
        reg_dir = reg_dirs[0]
        self.assertTrue((reg_dir / "regression.md").exists(), "regression.md 应在 flow regressions 目录下")
        self.assertTrue((reg_dir / "analysis.md").exists(), "analysis.md 应在 flow regressions 目录下")
        self.assertTrue((reg_dir / "decision.md").exists(), "decision.md 应在 flow regressions 目录下")
        self.assertTrue((reg_dir / "meta.yaml").exists(), "meta.yaml 应在 flow regressions 目录下")

    def test_create_regression_flat_no_old_regressions_dir(self) -> None:
        """方向C: artifacts/req-dir/regressions/ 子目录不应被创建（机器型文档不落 artifacts）."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-40", "test req 40")
        create_regression(self.root, "some regression flat")

        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("test req 40") or "test-req-40"
        artifacts_req_dir = self.root / "artifacts" / "main" / "requirements" / f"req-40-{slug}"
        regressions_legacy_dir = artifacts_req_dir / "regressions"
        self.assertFalse(regressions_legacy_dir.exists(), "方向C: artifacts/ 下不应建 regressions/ 目录（机器型文档落 flow）")

    def test_create_regression_flat_placeholder_brief_in_artifacts(self) -> None:
        """方向C: artifacts/ req 根目录下不应创建 回归简报.md placeholder（废弃四类 brief）."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-39", "test req 39")
        create_regression(self.root, "brief placeholder regression")

        from harness_workflow.slug import slugify_preserve_unicode
        slug = slugify_preserve_unicode("test req 39") or "test-req-39"
        req_dir = self.root / "artifacts" / "main" / "requirements" / f"req-39-{slug}"
        # 方向C: 不应在 artifacts/ 下创建 回归简报.md placeholder
        brief_files = list(req_dir.glob("reg-*-回归简报.md"))
        self.assertFalse(brief_files, "方向C: 不应在 artifacts/ 下创建 回归简报.md placeholder（废弃四类 brief）")

    def test_create_regression_legacy_path_for_req_before_39(self) -> None:
        """方向C: req-38（原 legacy 区间）也走 flow layout，regression 落 flow/requirements/req-38-*/regressions/."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-38", "test req 38 legacy")
        rc = create_regression(self.root, "legacy regression issue")
        self.assertEqual(rc, 0)

        # 方向C: regression 在 flow/requirements/req-38-*/regressions/（不在 artifacts/regressions/）
        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-38-*"))
        self.assertTrue(req_dirs, "flow/requirements/ 下应存在 req-38-* 目录")
        reg_dirs = list((req_dirs[0] / "regressions").glob("reg-*"))
        self.assertTrue(reg_dirs, "方向C: req-38 regression 应在 flow/requirements/req-38-*/regressions/ 下")
        reg_dir = reg_dirs[0]
        self.assertTrue((reg_dir / "regression.md").exists(), "regression.md 应在 flow 目录下")

    def test_create_regression_legacy_no_state_sessions(self) -> None:
        """方向C: req-37（原 legacy 区间）的 regression 不应在 state/sessions/ 下创建目录."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo(self.root, "req-37", "test req 37 legacy")
        create_regression(self.root, "legacy regression no state sessions")

        state_reg_base = self.root / ".workflow" / "state" / "sessions" / "req-37" / "regressions"
        self.assertFalse(state_reg_base.exists(), "方向C: 不应在 state/sessions/ 下创建 regressions 目录（废弃 state-flat 分支）")


if __name__ == "__main__":
    unittest.main()
