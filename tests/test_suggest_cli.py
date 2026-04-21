"""Unit tests for harness suggest CLI（req-28 / chg-01，覆盖 AC-15）。

覆盖三条核心断言：

- `delete_suggestion` 对无 YAML frontmatter 的 sug 文件，可通过 `sug-NN`
  （filename fallback）删除；
- `apply_suggestion` 同理——无 frontmatter 的 sug 能被 apply（翻转 status
  并创建 requirement）；
- `create_suggestion` 在当前目录为空、`archive/` 下仅存在 `sug-20-*.md`
  的情况下，新建文件编号必须为 `sug-21`（跨 archive 单调递增）。

Helper 层直接调用 workflow_helpers 函数，不跑真 CLI；tempdir 隔离；
通过 monkey-patch `_get_git_branch` 将 branch 固定为 `main`，避免
依赖测试机 git 状态。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    """构造最小 harness 工作区，覆盖 ensure_harness_root 所需路径。"""
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(root: Path) -> None:
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'operation_type: "requirement"',
                'operation_target: ""',
                'current_requirement: ""',
                'stage: "done"',
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


class SuggestCLITest(unittest.TestCase):
    """req-28 / chg-01：harness suggest CLI 的 3 条关键行为。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-suggest-cli-"))
        self.root = _make_harness_workspace(self.tempdir)
        _write_runtime(self.root)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        # 屏蔽 create_requirement 的交互/子进程副作用
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    # ---------- Assertion (a): delete by short id without frontmatter ----------
    def test_delete_by_short_id_works_without_frontmatter(self) -> None:
        """无 YAML frontmatter 的 sug，`delete_suggestion('sug-99')` 必须能删除。

        bug 活证：旧实现仅按 frontmatter `id:` 匹配，无 frontmatter 的
        sug 永远走 `Suggestion not found` 分支。
        """
        from harness_workflow.workflow_helpers import delete_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        sug_path = sug_dir / "sug-99-demo-no-frontmatter.md"
        sug_path.write_text(
            "# 一条没有 frontmatter 的历史建议\n\n正文内容。\n",
            encoding="utf-8",
        )

        self.assertTrue(sug_path.exists(), "前置：sug 文件应存在")
        rc = delete_suggestion(self.root, "sug-99")
        self.assertEqual(rc, 0)
        self.assertFalse(
            sug_path.exists(),
            "sug-99 应被删除（filename fallback 生效）",
        )

    # ---------- Assertion (b): apply by short id without frontmatter ----------
    def test_apply_by_short_id_works_without_frontmatter(self) -> None:
        """无 YAML frontmatter 的 sug，`apply_suggestion('sug-88')` 必须能应用。

        apply 成功的判据：返回值为 0，且 sug 文件被搬到 `archive/`（bugfix-3
        起成功 apply 后必须归档源文件，不再留在 suggestions/ 根下）。
        """
        from harness_workflow.workflow_helpers import apply_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        sug_path = sug_dir / "sug-88-apply-demo.md"
        sug_path.write_text(
            "修复 suggest apply 的兼容路径\n\n详细说明……\n",
            encoding="utf-8",
        )

        # Patch create_requirement 避免真实创建需求产物，聚焦 apply 的匹配逻辑
        with mock.patch(
            "harness_workflow.workflow_helpers.create_requirement",
            return_value=0,
        ) as create_mock:
            rc = apply_suggestion(self.root, "sug-88")

        self.assertEqual(rc, 0, "apply_suggestion 应返回 0（filename fallback 生效）")
        self.assertTrue(create_mock.called, "apply 成功时应调用 create_requirement")
        # bugfix-3：apply 成功后源 sug 文件应被 move 到 archive/，源路径不再存在
        self.assertFalse(
            sug_path.exists(),
            "apply 成功后原 sug 应被归档（bugfix-3 行为）",
        )
        archived = sug_dir / "archive" / "sug-88-apply-demo.md"
        self.assertTrue(
            archived.exists(),
            f"归档后的 sug 文件应存在于 {archived}",
        )

    # ---------- Assertion (c): create numbering monotonic across archive ----------
    def test_create_suggestion_numbering_monotonic_across_archive(self) -> None:
        """archive/ 下存在 `sug-20-*.md`，当前目录为空，新建应得 `sug-21-*`。

        bug 活证：旧实现仅扫当前目录，清空后会从 sug-01 重新计数，与 archive
        历史冲突。
        """
        from harness_workflow.workflow_helpers import create_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        archive_dir = sug_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        (archive_dir / "sug-20-old-archived.md").write_text(
            "---\nid: sug-20\nstatus: archived\n---\n\n归档正文。\n",
            encoding="utf-8",
        )

        # 前置：当前目录应为空（sug-*.md 个数为 0）
        current_files = list(sug_dir.glob("sug-*.md"))
        self.assertEqual(
            len(current_files),
            0,
            f"前置：suggestions/ 当前目录应为空，实际 {current_files}",
        )

        # req-31 / chg-01 Step 1.2：create_suggestion 现在要求 title 必填（契约 6）。
        rc = create_suggestion(
            self.root,
            "跨 archive 单调递增回归样本",
            title="跨 archive 单调递增回归样本",
        )
        self.assertEqual(rc, 0)

        new_files = sorted(sug_dir.glob("sug-*.md"))
        self.assertEqual(
            len(new_files),
            1,
            f"应新建一个 sug 文件，实际 {new_files}",
        )
        created_name = new_files[0].name
        self.assertTrue(
            created_name.startswith("sug-21-"),
            f"新建 sug 应以 sug-21- 开头（跨 archive 递增），实际 {created_name}",
        )


if __name__ == "__main__":
    unittest.main()
