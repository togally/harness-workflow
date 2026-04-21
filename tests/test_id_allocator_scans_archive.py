"""Tests for req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 4（sug-19）.

覆盖 `_next_req_id` / `_next_bugfix_id` 扩展到扫描归档树：
- test_next_req_id_considers_archived_requirements：归档 req-50 + 活跃 req-10 → next == "req-51".
- test_next_bugfix_id_considers_archived：归档 bugfix-7 + 活跃 bugfix-2 → next == "bugfix-8".
- test_next_req_id_ignores_non_matching_dirs：随机目录名不影响计数。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class IdAllocatorArchiveScanTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir(parents=True)
        # 固定 branch=main，避免依赖 test runner 的 git 上下文
        from harness_workflow import workflow_helpers
        patcher = mock.patch.object(
            workflow_helpers,
            "_get_git_branch",
            return_value="main",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_next_req_id_considers_archived_requirements(self) -> None:
        from harness_workflow.workflow_helpers import _next_req_id

        # 活跃：req-10
        (self.root / "artifacts" / "main" / "requirements" / "req-10-live").mkdir(parents=True)
        # 归档（primary 形态）：req-50
        (self.root / "artifacts" / "main" / "archive" / "requirements" / "req-50-old").mkdir(parents=True)
        # legacy 归档形态：req-25
        (self.root / ".workflow" / "flow" / "archive" / "main" / "req-25-legacy").mkdir(parents=True)

        self.assertEqual(_next_req_id(self.root), "req-51")

    def test_next_bugfix_id_considers_archived(self) -> None:
        from harness_workflow.workflow_helpers import _next_bugfix_id

        (self.root / "artifacts" / "main" / "bugfixes" / "bugfix-2-live").mkdir(parents=True)
        (self.root / "artifacts" / "main" / "archive" / "bugfixes" / "bugfix-7-old").mkdir(parents=True)

        self.assertEqual(_next_bugfix_id(self.root), "bugfix-8")

    def test_next_req_id_ignores_non_matching_dirs(self) -> None:
        from harness_workflow.workflow_helpers import _next_req_id

        (self.root / "artifacts" / "main" / "requirements" / "random-dir").mkdir(parents=True)
        (self.root / "artifacts" / "main" / "archive" / "requirements" / "notes").mkdir(parents=True)
        # 无任何 req-NN 目录 → 起点 req-01
        self.assertEqual(_next_req_id(self.root), "req-01")


if __name__ == "__main__":
    unittest.main()
