"""Tests for req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 4（sug-24）.

覆盖 regression reg-NN 的独立 title 源：
- test_create_regression_requires_explicit_title：全参皆空 → SystemExit。
- test_regression_title_independent_from_parent_req：parent req title="foo" + reg
  title="bar" → reg 目录 slug 以 "bar" 为准，runtime["current_regression_title"] == "bar"。
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo(root: Path, parent_req_id: str = "req-99", parent_req_title: str = "parent req title foo") -> None:
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements" / f"{parent_req_id}-demo").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{parent_req_id}"',
            f'current_requirement_title: "{parent_req_title}"',
            'stage: "regression"',
            'operation_type: "requirement"',
            f'operation_target: "{parent_req_id}"',
            'conversation_mode: "open"',
            'active_requirements: []',
            "",
        ]),
        encoding="utf-8",
    )
    # parent req state yaml
    (root / ".workflow" / "state" / "requirements" / f"{parent_req_id}-demo.yaml").write_text(
        "\n".join([
            f'id: "{parent_req_id}"',
            f'title: "{parent_req_title}"',
            'stage: "executing"',
            "",
        ]),
        encoding="utf-8",
    )


class RegressionIndependentTitleTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        _init_harness_repo(self.root)

    def test_create_regression_requires_explicit_title(self) -> None:
        """全参皆空 → SystemExit（不再 fallback 到 parent req title）。"""
        from harness_workflow.workflow_helpers import create_regression

        with self.assertRaises(SystemExit):
            create_regression(self.root, None, None, None)

    def test_regression_title_independent_from_parent_req(self) -> None:
        """parent req title="parent req title foo" + reg title="bar issue" → reg 独立，
        runtime.current_regression_title == "bar issue"，slug 不包含 parent title。"""
        from harness_workflow.workflow_helpers import (
            create_regression,
            load_requirement_runtime,
        )

        rc = create_regression(self.root, "bar issue")
        self.assertEqual(rc, 0)
        runtime = load_requirement_runtime(self.root)
        # reg title 必须是自己的，不复用 parent
        self.assertEqual(runtime.get("current_regression_title", ""), "bar issue")
        self.assertTrue(runtime.get("current_regression", "").startswith("reg-"))

        # 目录 slug 必须以 "bar" 为主（parent title "parent req title foo" 不应出现）
        regressions_dirs = list(
            (self.root / "artifacts" / "main" / "requirements").glob("req-*/regressions/reg-*")
        )
        self.assertTrue(regressions_dirs, "regression 目录必须存在")
        reg_dir_name = regressions_dirs[0].name
        self.assertIn("bar", reg_dir_name.lower())
        self.assertNotIn("parent", reg_dir_name.lower())


if __name__ == "__main__":
    unittest.main()
