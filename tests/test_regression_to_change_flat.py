"""Tests updated for bugfix-11 方向C（废弃三段式分水岭）.

原测试覆盖 Scope-D: regression --change 对 req-39+ 走扁平路径。
bugfix-11 方向C 废弃三段式分水岭后：
- 所有 req 一律走 flow layout
- regression --change 对所有 req（含原 req-38/37 legacy）也走 flow layout
- chg-id 从 flow req_dir/changes/chg-* 分配（不再扫 state/sessions）
- req-38 的 regression --change 也走 flow layout（废弃 legacy artifacts/changes/ 路径）
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo_with_regression(
    root: Path,
    req_id: str,
    req_title: str = "test req",
    regression_id: str = "reg-03",
) -> tuple[Path, Path]:
    """Create minimal harness repo with an active regression. Returns (artifacts_req_dir, flow_req_dir)."""
    from harness_workflow.slug import slugify_preserve_unicode

    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".workflow" / "context" / "experience").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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
            f'current_regression: "{regression_id}"',
            'current_regression_title: "test regression"',
            'stage: "acceptance"',
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
            'stage: "acceptance"',
            "",
        ]),
        encoding="utf-8",
    )
    return req_dir, flow_req_dir


class RegressionToChangeFlatTest(unittest.TestCase):
    """bugfix-11 方向C: regression --change 对所有 req 走 flow layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_regression_change_creates_flat_path_for_req39(self) -> None:
        """方向C: regression --change 对 req-39 在 flow/requirements/req-39-*/changes/chg-NN/ 创建目录."""
        from harness_workflow.workflow_helpers import regression_action

        _, flow_req_dir = _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        rc = regression_action(
            self.root,
            change_title="new change from regression",
        )
        self.assertEqual(rc, 0)

        # 方向C: 机器型文档落 flow/requirements/req-39-*/changes/
        chg_dirs = list((flow_req_dir / "changes").glob("chg-*"))
        self.assertTrue(chg_dirs, "方向C: regression --change 对 req-39 应在 flow/requirements/req-39-*/changes/chg-*/ 创建目录")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 flow chg 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 flow chg 目录下")

    def test_regression_change_no_legacy_changes_dir_for_req39(self) -> None:
        """方向C: regression --change 对 req-39 不应在 artifacts/changes/ 子目录下创建文件."""
        from harness_workflow.workflow_helpers import regression_action

        req_dir, _ = _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        regression_action(
            self.root,
            change_title="no legacy changes dir",
        )
        legacy_changes_dir = req_dir / "changes"
        self.assertFalse(legacy_changes_dir.exists(), "方向C: regression --change 不应创建 artifacts/changes/ 目录")

    def test_regression_change_correct_chg_id_with_existing_state_sessions(self) -> None:
        """方向C: regression --change 对 req-39 + 已有 chg-01..chg-07 应分配 chg-08（扫 flow changes）."""
        from harness_workflow.workflow_helpers import regression_action

        _, flow_req_dir = _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        # 预置 chg-01..chg-07 在 flow/requirements/req-39-*/changes/
        for i in range(1, 8):
            (flow_req_dir / "changes" / f"chg-{i:02d}-existing").mkdir(parents=True)

        regression_action(
            self.root,
            change_title="chg id allocation test",
        )
        chg_dirs = sorted(
            [d.name for d in (flow_req_dir / "changes").iterdir()
             if d.is_dir() and not d.name.endswith("-existing")]
        )
        self.assertEqual(len(chg_dirs), 1, "应新增恰好 1 个新 chg 目录")
        new_dir = chg_dirs[0]
        self.assertTrue(new_dir.startswith("chg-08"), f"新 chg 应为 chg-08-..., 实际: {new_dir}")

    def test_regression_change_clears_current_regression(self) -> None:
        """方向C: regression --change 完成后 runtime.current_regression 应被清空."""
        from harness_workflow.workflow_helpers import regression_action, load_requirement_runtime

        _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        regression_action(self.root, change_title="clear regression id test")
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime.get("current_regression", "")), "", "current_regression 应被清空")

    def test_regression_change_legacy_req_stays_legacy(self) -> None:
        """方向C: regression --change 对 req-38（原 legacy）也走 flow layout（不走 artifacts/changes/）."""
        from harness_workflow.workflow_helpers import regression_action

        req_dir, flow_req_dir = _init_harness_repo_with_regression(self.root, "req-38", "legacy req")
        rc = regression_action(self.root, change_title="legacy regression change")
        self.assertEqual(rc, 0)

        # 方向C: req-38 也走 flow layout（废弃 legacy artifacts/changes/ 路径）
        chg_dirs = list((flow_req_dir / "changes").glob("chg-*"))
        self.assertTrue(chg_dirs, "方向C: req-38 regression --change 也应在 flow changes/ 下（废弃 legacy 路径）")

        # 旧 artifacts/changes/ 不应被创建
        legacy_changes_dir = req_dir / "changes"
        self.assertFalse(
            legacy_changes_dir.exists(),
            "方向C: req-38 regression --change 不应创建 artifacts/changes/（废弃 legacy 分支）",
        )


if __name__ == "__main__":
    unittest.main()
