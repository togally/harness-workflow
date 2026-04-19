"""Unit tests for `create_regression` / `regression_action` helpers.

Covers req-26 / chg-01 acceptance criteria:

- AC-01: `regression_action(..., confirm=True)` 不得清空
  `runtime.current_regression`；随后 `regression_action(..., to_testing=True)`
  仍能识别并消费 regression。
- AC-04: `create_regression(...)` 产出目录命名必须使用 kebab-case 且以
  `reg-NN-` 前缀开头，不得包含空格或全角标点。

这些用例直接调用 helper 层函数，避免真跑 `harness regression` CLI 污染当前
仓库 runtime 状态（subagent briefing 的硬约束之一）。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    """在 tmpdir 下构造一个最小可用的 harness workspace，使 helper 不抛
    `Harness workspace is missing`。不运行 `install`，只铺必需的目录与 runtime.yaml。"""
    import json

    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'current_requirement: ""',
                'stage: ""',
                'conversation_mode: "open"',
                'locked_requirement: ""',
                'locked_stage: ""',
                'current_regression: ""',
                "ff_mode: false",
                "ff_stage_history: []",
                "active_requirements: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


class SlugUtilTest(unittest.TestCase):
    """Unit test for the shared `slugify_preserve_unicode` util (chg-02 reuses)."""

    def test_english_kebab_case(self) -> None:
        from harness_workflow.slug import slugify_preserve_unicode

        self.assertEqual(slugify_preserve_unicode("issue with spaces"), "issue-with-spaces")

    def test_strip_punctuation(self) -> None:
        from harness_workflow.slug import slugify_preserve_unicode

        self.assertEqual(slugify_preserve_unicode("Fix: Layout Bug?!"), "fix-layout-bug")
        self.assertEqual(slugify_preserve_unicode('weird/name\\with:illegal*chars'), "weird-name-with-illegal-chars")

    def test_preserve_cjk(self) -> None:
        from harness_workflow.slug import slugify_preserve_unicode

        self.assertEqual(slugify_preserve_unicode("uav-split 拆分"), "uav-split-拆分")
        self.assertEqual(slugify_preserve_unicode("完全中文问题"), "完全中文问题")
        # 全角冒号必须被吃掉
        self.assertEqual(slugify_preserve_unicode("修复：回归目录"), "修复-回归目录")

    def test_empty_input(self) -> None:
        from harness_workflow.slug import slugify_preserve_unicode

        self.assertEqual(slugify_preserve_unicode(""), "")
        self.assertEqual(slugify_preserve_unicode("   "), "")
        self.assertEqual(slugify_preserve_unicode("???"), "")


class CreateRegressionDirNamingTest(unittest.TestCase):
    """AC-04: regression 产出目录必须 kebab-case 且以 reg-NN- 前缀开头。"""

    def setUp(self) -> None:
        import tempfile

        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-regression-dir-test-"))
        self.root = _make_harness_workspace(self.tempdir, language="english")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tempdir)

    def test_spaces_become_kebab_case_with_reg_prefix(self) -> None:
        from harness_workflow.workflow_helpers import create_regression, load_requirement_runtime

        rc = create_regression(self.root, "issue with spaces")
        self.assertEqual(rc, 0)

        # current_regression 应为纯 reg-NN（便于后续 --confirm / --testing 引用）
        runtime = load_requirement_runtime(self.root)
        reg_id = str(runtime["current_regression"])
        self.assertRegex(reg_id, r"^reg-\d{2}$")

        # 产出目录位于 artifacts/main/regressions/ 下（当前无 current_requirement，兜底到 artifacts/main/regressions）
        import re

        regressions_base = self.root / "artifacts" / "main" / "regressions"
        self.assertTrue(regressions_base.exists())
        dirs = [d for d in regressions_base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        self.assertRegex(dirs[0].name, r"^reg-\d{2}-issue-with-spaces$")
        self.assertNotIn(" ", dirs[0].name)

    def test_cjk_title_preserved_with_reg_prefix(self) -> None:
        from harness_workflow.workflow_helpers import create_regression

        rc = create_regression(self.root, "确认问题：按钮点击异常")
        self.assertEqual(rc, 0)

        regressions_base = self.root / "artifacts" / "main" / "regressions"
        dirs = [d.name for d in regressions_base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        # 全角冒号被过滤为 `-`，中文保留，带 reg-NN 前缀
        self.assertTrue(dirs[0].startswith("reg-"))
        self.assertIn("确认问题", dirs[0])
        self.assertIn("按钮点击异常", dirs[0])
        # 禁止空格与全角冒号
        self.assertNotIn(" ", dirs[0])
        self.assertNotIn("：", dirs[0])

    def test_sequential_ids(self) -> None:
        from harness_workflow.workflow_helpers import create_regression

        create_regression(self.root, "first issue")
        create_regression(self.root, "second issue")
        regressions_base = self.root / "artifacts" / "main" / "regressions"
        names = sorted(d.name for d in regressions_base.iterdir() if d.is_dir())
        self.assertEqual(len(names), 2)
        self.assertTrue(names[0].startswith("reg-01-"))
        self.assertTrue(names[1].startswith("reg-02-"))


class ConfirmPreservesStateTest(unittest.TestCase):
    """AC-01: `--confirm` 不得消费 regression 状态；后续 `--testing` 仍可用。"""

    def setUp(self) -> None:
        import tempfile

        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-regression-confirm-test-"))
        self.root = _make_harness_workspace(self.tempdir, language="english")

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.tempdir)

    def test_confirm_then_testing_flow(self) -> None:
        from harness_workflow.workflow_helpers import (
            create_regression,
            load_requirement_runtime,
            regression_action,
        )

        # 1. 创建 regression
        create_regression(self.root, "demo issue")
        runtime = load_requirement_runtime(self.root)
        reg_id_before = str(runtime["current_regression"])
        self.assertTrue(reg_id_before)

        # 2. --confirm 后 current_regression 必须保留
        rc = regression_action(self.root, confirm=True)
        self.assertEqual(rc, 0)
        runtime = load_requirement_runtime(self.root)
        reg_id_after_confirm = str(runtime["current_regression"])
        self.assertEqual(reg_id_after_confirm, reg_id_before, "--confirm must NOT clear current_regression")

        # 2a. meta.yaml 里 status 应被更新为 confirmed（若目录可定位）
        regressions_base = self.root / "artifacts" / "main" / "regressions"
        dirs = [d for d in regressions_base.iterdir() if d.is_dir()]
        self.assertEqual(len(dirs), 1)
        meta_path = dirs[0] / "meta.yaml"
        self.assertTrue(meta_path.exists())
        meta_text = meta_path.read_text(encoding="utf-8")
        self.assertIn('status: "confirmed"', meta_text)

        # 3. --testing 仍能继续消费该 regression，不得报 "No active regression"
        rc = regression_action(self.root, to_testing=True)
        self.assertEqual(rc, 0)
        runtime = load_requirement_runtime(self.root)
        # --testing 是真正消费 regression 的动作，runtime 应被清；stage 应回到 testing
        self.assertEqual(str(runtime["current_regression"]), "")
        self.assertEqual(str(runtime["stage"]), "testing")

    def test_testing_without_prior_confirm_still_requires_active_regression(self) -> None:
        """守住原有保护：无活跃 regression 时 --testing 仍报错。"""
        from harness_workflow.workflow_helpers import regression_action

        with self.assertRaises(SystemExit):
            regression_action(self.root, to_testing=True)


if __name__ == "__main__":
    unittest.main()
