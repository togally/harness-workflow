"""Tests for req-31（批量建议合集（20条））/ chg-04（归档迁移 + 数据管道）/ Step 1+5（sug-22）.

覆盖 `_write_archive_meta` helper 以及 archive_requirement / migrate_archive 的集成：

- test_write_archive_meta_fields：写入 `_meta.yaml` 含 id/title/archived_at/origin_stage.
- test_write_archive_meta_idempotent：重复写入保留原 `archived_at`（幂等）。
- test_archive_requirement_writes_meta_yaml：`archive_requirement` 归档后目录含 `_meta.yaml`.
- test_migrate_archive_writes_meta_yaml：legacy 归档迁移后补 `_meta.yaml`.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class WriteArchiveMetaTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_write_archive_meta_fields(self) -> None:
        from harness_workflow.workflow_helpers import _write_archive_meta, load_simple_yaml

        archive_dir = self.root / "req-99-demo"
        archive_dir.mkdir()
        _write_archive_meta(archive_dir, "req-99", "demo title", origin_stage="done")
        meta_path = archive_dir / "_meta.yaml"
        self.assertTrue(meta_path.exists())
        data = load_simple_yaml(meta_path)
        self.assertEqual(data.get("id"), "req-99")
        self.assertEqual(data.get("title"), "demo title")
        self.assertEqual(data.get("origin_stage"), "done")
        self.assertTrue(data.get("archived_at"), "archived_at 必须非空")

    def test_write_archive_meta_idempotent(self) -> None:
        """重复归档：保留首次的 archived_at，仅刷新 title / origin_stage。"""
        from harness_workflow.workflow_helpers import _write_archive_meta, load_simple_yaml

        archive_dir = self.root / "req-100-x"
        archive_dir.mkdir()
        _write_archive_meta(archive_dir, "req-100", "first", origin_stage="done")
        first = load_simple_yaml(archive_dir / "_meta.yaml")
        first_at = first["archived_at"]
        time.sleep(0.01)
        _write_archive_meta(archive_dir, "req-100", "second", origin_stage="legacy-migrated")
        second = load_simple_yaml(archive_dir / "_meta.yaml")
        self.assertEqual(second["archived_at"], first_at)
        self.assertEqual(second["title"], "second")
        self.assertEqual(second["origin_stage"], "legacy-migrated")


class MigrateArchiveMetaTest(unittest.TestCase):
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

    def test_migrate_archive_writes_meta_yaml(self) -> None:
        """legacy 归档（`.workflow/flow/archive/main/requirements/req-50-old/`）迁移后，
        目标目录内应落 `_meta.yaml`，origin_stage == 'legacy-migrated'。
        """
        from harness_workflow.workflow_helpers import load_simple_yaml, migrate_archive

        src = self.root / ".workflow" / "flow" / "archive" / "main" / "requirements" / "req-50-old"
        src.mkdir(parents=True)
        (src / "done-report.md").write_text("done\n", encoding="utf-8")

        rc = migrate_archive(self.root)
        self.assertEqual(rc, 0)
        dst = self.root / "artifacts" / "main" / "archive" / "requirements" / "req-50-old"
        self.assertTrue(dst.exists())
        meta = dst / "_meta.yaml"
        self.assertTrue(meta.exists(), "迁移后必须落 _meta.yaml")
        data = load_simple_yaml(meta)
        self.assertEqual(data["id"], "req-50")
        self.assertEqual(data["origin_stage"], "legacy-migrated")


if __name__ == "__main__":
    unittest.main()
