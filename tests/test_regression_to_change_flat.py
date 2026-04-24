"""Tests for Scope-D: regression --change flat layout path.

chg-08（stage 耗时 + token 消耗统计 + usage-reporter 对人报告）/
Scope-D：harness regression --change 对 req-id >= 39 走扁平路径 + 正确 chg-id。

补齐 chg-07（create_requirement CLI 路径对齐补齐 + pytest）漏网：
- regression --change 调用 create_change 时，req-39+ 应走 flat layout
- chg-id 应正确从 state/sessions/{req-id}/chg-* 分配（不被 legacy changes/ 干扰）
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
) -> Path:
    """Create minimal harness repo with an active regression for req-id >= 39."""
    from harness_workflow.slug import slugify_preserve_unicode

    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)
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
    return req_dir


class RegressionToChangeFlatTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_regression_change_creates_flat_path_for_req39(self) -> None:
        """regression --change 对 req-39 应在 state/sessions/req-39/chg-NN/ 创建 change 目录（扁平路径）。"""
        from harness_workflow.workflow_helpers import regression_action

        _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        rc = regression_action(
            self.root,
            change_title="new change from regression",
        )
        self.assertEqual(rc, 0)

        # 验证扁平路径：机器型文档落 state/sessions/req-39/chg-NN/
        state_sessions = self.root / ".workflow" / "state" / "sessions" / "req-39"
        chg_dirs = [d for d in state_sessions.iterdir() if d.is_dir() and d.name.startswith("chg-")]
        self.assertTrue(chg_dirs, "regression --change 对 req-39 应在 state/sessions/req-39/chg-*/ 创建目录")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 flat chg 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 flat chg 目录下")

    def test_regression_change_no_legacy_changes_dir_for_req39(self) -> None:
        """regression --change 对 req-39 不应在 artifacts/changes/ 子目录下创建文件。"""
        from harness_workflow.workflow_helpers import regression_action

        req_dir = _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        regression_action(
            self.root,
            change_title="no legacy changes dir",
        )
        legacy_changes_dir = req_dir / "changes"
        self.assertFalse(legacy_changes_dir.exists(), "req-39+ regression --change 不应创建 legacy changes/ 目录")

    def test_regression_change_correct_chg_id_with_existing_state_sessions(self) -> None:
        """regression --change 对 req-39 + 已有 chg-01..chg-07 应分配 chg-08（扫 state/sessions）。"""
        from harness_workflow.workflow_helpers import regression_action

        _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        # 预置 chg-01..chg-07 在 state/sessions/req-39/
        sessions_dir = self.root / ".workflow" / "state" / "sessions" / "req-39"
        for i in range(1, 8):
            (sessions_dir / f"chg-{i:02d}-existing").mkdir(parents=True)

        regression_action(
            self.root,
            change_title="chg id allocation test",
        )
        chg_dirs = sorted(
            [d.name for d in sessions_dir.iterdir() if d.is_dir() and d.name.startswith("chg-")
             and not d.name.endswith("-existing")]
        )
        self.assertEqual(len(chg_dirs), 1, "应新增恰好 1 个新 chg 目录")
        new_dir = chg_dirs[0]
        self.assertTrue(new_dir.startswith("chg-08"), f"新 chg 应为 chg-08-..., 实际: {new_dir}")

    def test_regression_change_clears_current_regression(self) -> None:
        """regression --change 完成后 runtime.current_regression 应被清空。"""
        from harness_workflow.workflow_helpers import regression_action, load_requirement_runtime

        _init_harness_repo_with_regression(self.root, "req-39", "flat test req")
        regression_action(self.root, change_title="clear regression id test")
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime.get("current_regression", "")), "", "current_regression 应被清空")

    def test_regression_change_legacy_req_stays_legacy(self) -> None:
        """regression --change 对 req-38（legacy）仍走 artifacts/changes/ 路径（不受本修复影响）。"""
        from harness_workflow.workflow_helpers import regression_action

        req_dir = _init_harness_repo_with_regression(self.root, "req-38", "legacy req")
        rc = regression_action(self.root, change_title="legacy regression change")
        self.assertEqual(rc, 0)

        legacy_changes_dir = req_dir / "changes"
        self.assertTrue(legacy_changes_dir.exists(), "req-38 regression --change 应仍走 legacy changes/ 路径")
        chg_dirs = list(legacy_changes_dir.glob("chg-*"))
        self.assertTrue(chg_dirs, "legacy changes/ 下应有 chg-* 目录")


if __name__ == "__main__":
    unittest.main()
