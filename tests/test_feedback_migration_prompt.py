"""Tests for req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 3（sug-20）.

覆盖 `update_repo` 对 `.harness/feedback.jsonl → .workflow/state/feedback/feedback.jsonl`
的迁移行为：迁移成功后必须在 stderr 打印 git 变更提示，引导用户 commit。

- test_update_repo_prints_git_hint_after_feedback_migration：迁移触发 → stderr 含提示。
- test_update_repo_no_hint_without_migration：无 legacy feedback → 不打印提示。
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class FeedbackMigrationPromptTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        # minimal harness workspace
        (self.root / ".workflow" / "state").mkdir(parents=True)
        (self.root / ".workflow" / "context").mkdir(parents=True)
        (self.root / ".codex" / "harness").mkdir(parents=True)
        (self.root / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        # platforms.yaml with active_agent for deterministic update_repo behavior
        (self.root / ".workflow" / "state" / "platforms.yaml").write_text(
            "active_agent: codex\n",
            encoding="utf-8",
        )

    def test_update_repo_prints_git_hint_after_feedback_migration(self) -> None:
        from harness_workflow.workflow_helpers import update_repo

        # Seed legacy feedback at .harness/feedback.jsonl
        legacy = self.root / ".harness" / "feedback.jsonl"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('{"evt": "legacy"}\n', encoding="utf-8")

        stderr_buf = io.StringIO()
        stdout_buf = io.StringIO()
        with redirect_stderr(stderr_buf), redirect_stdout(stdout_buf):
            rc = update_repo(self.root, check=False)
        self.assertEqual(rc, 0)
        err = stderr_buf.getvalue()
        self.assertIn("migrated .harness/feedback.jsonl", err)
        # 关键断言：含 git 变更提示（用户自证 sug-20 意图）
        self.assertIn("git status", err)

    def test_update_repo_no_hint_without_migration(self) -> None:
        from harness_workflow.workflow_helpers import update_repo

        stderr_buf = io.StringIO()
        stdout_buf = io.StringIO()
        with redirect_stderr(stderr_buf), redirect_stdout(stdout_buf):
            rc = update_repo(self.root, check=False)
        self.assertEqual(rc, 0)
        # 无迁移 → 不打印 feedback 迁移提示
        self.assertNotIn("migrated .harness/feedback.jsonl", stderr_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
