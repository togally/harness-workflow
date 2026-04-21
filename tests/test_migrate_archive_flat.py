"""Tests for req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 2（sug-08）.

覆盖 `migrate_archive` 对扁平格式历史归档（``<branch>/<dir>`` 直接挂在 legacy archive
根下、无 ``requirements/`` / ``bugfixes/`` 中间层）的支持：

- test_migrate_archive_flat_requirement：`main/req-50-old/` → `artifacts/main/archive/requirements/req-50-old/`.
- test_migrate_archive_flat_bugfix：`main/bugfix-7-x/` → `artifacts/main/archive/bugfixes/bugfix-7-x/`.
- test_migrate_archive_flat_skips_non_id_dirs：`main/random-dir/` 保留原位不迁。
- test_migrate_archive_flat_dry_run：dry-run 模式不实际移动。
- test_migrate_archive_flat_idempotent：重复运行 noop。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class MigrateArchiveFlatTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir(parents=True)
        from harness_workflow import workflow_helpers
        patcher = mock.patch.object(
            workflow_helpers,
            "_get_git_branch",
            return_value="main",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def _seed_flat(self, name: str, body: str = "# x\n") -> Path:
        src = self.root / ".workflow" / "flow" / "archive" / "main" / name
        src.mkdir(parents=True)
        (src / "done-report.md").write_text(body, encoding="utf-8")
        return src

    def test_migrate_archive_flat_requirement(self) -> None:
        from harness_workflow.workflow_helpers import migrate_archive

        self._seed_flat("req-50-old-title")
        rc = migrate_archive(self.root)
        self.assertEqual(rc, 0)
        dst = self.root / "artifacts" / "main" / "archive" / "requirements" / "req-50-old-title"
        self.assertTrue(dst.exists())
        self.assertTrue((dst / "done-report.md").exists())
        self.assertTrue((dst / "_meta.yaml").exists())

    def test_migrate_archive_flat_bugfix(self) -> None:
        from harness_workflow.workflow_helpers import migrate_archive

        self._seed_flat("bugfix-7-xyz", body="# bug\n")
        rc = migrate_archive(self.root)
        self.assertEqual(rc, 0)
        dst = self.root / "artifacts" / "main" / "archive" / "bugfixes" / "bugfix-7-xyz"
        self.assertTrue(dst.exists())

    def test_migrate_archive_flat_skips_non_id_dirs(self) -> None:
        from harness_workflow.workflow_helpers import migrate_archive

        self._seed_flat("random-dir")
        rc = migrate_archive(self.root)
        self.assertEqual(rc, 0)
        # 源保留不动
        self.assertTrue((self.root / ".workflow" / "flow" / "archive" / "main" / "random-dir").exists())

    def test_migrate_archive_flat_dry_run(self) -> None:
        from harness_workflow.workflow_helpers import migrate_archive

        self._seed_flat("req-60-dry")
        rc = migrate_archive(self.root, dry_run=True)
        self.assertEqual(rc, 0)
        # 源保留
        self.assertTrue((self.root / ".workflow" / "flow" / "archive" / "main" / "req-60-dry").exists())
        # 目标未创建
        self.assertFalse(
            (self.root / "artifacts" / "main" / "archive" / "requirements" / "req-60-dry").exists()
        )

    def test_migrate_archive_flat_idempotent(self) -> None:
        from harness_workflow.workflow_helpers import migrate_archive

        self._seed_flat("req-70-ok")
        migrate_archive(self.root)
        # 第二次调用：源已清空 → nothing to migrate
        rc = migrate_archive(self.root)
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
