"""Tests for req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 3（sug-17）.

覆盖 `_auto_locate_repo_root` helper：
- test_auto_locate_finds_repo_root_from_subdir：在 `repo/src/sub/` 下搜到 `repo/.workflow/`.
- test_auto_locate_returns_start_when_already_at_root：本身就在 repo 根 → 返回自身。
- test_auto_locate_raises_when_no_repo_found：完全无 `.workflow/` 目录 → SystemExit + 清晰错误消息。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class AutoLocateRepoRootTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_root = Path(self._tmp.name)

    def test_auto_locate_finds_repo_root_from_subdir(self) -> None:
        from harness_workflow.cli import _auto_locate_repo_root

        repo = self.tmp_root / "repo"
        (repo / ".workflow" / "state").mkdir(parents=True)
        sub = repo / "src" / "nested"
        sub.mkdir(parents=True)
        located = _auto_locate_repo_root(sub)
        self.assertEqual(located.resolve(), repo.resolve())

    def test_auto_locate_returns_start_when_already_at_root(self) -> None:
        from harness_workflow.cli import _auto_locate_repo_root

        repo = self.tmp_root / "r2"
        (repo / ".workflow").mkdir(parents=True)
        self.assertEqual(_auto_locate_repo_root(repo).resolve(), repo.resolve())

    def test_auto_locate_raises_when_no_repo_found(self) -> None:
        from harness_workflow.cli import _auto_locate_repo_root

        # 全新 tmp，没有任何 .workflow/ 祖先
        with self.assertRaises(SystemExit) as ctx:
            _auto_locate_repo_root(self.tmp_root)
        self.assertIn(".workflow", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
