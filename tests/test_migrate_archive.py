"""Unit tests for ``migrate_archive`` helper (req-29 / chg-02, AC-04).

覆盖场景：

- happy path（requirement 归档）：legacy 下带分支前缀的 requirement 归档被搬到
  ``artifacts/{branch}/archive/requirements/<dir>``，源清空。
- happy path（bugfix 归档）：同上对 bugfixes 形态。
- dry-run：传 ``--dry-run`` 语义时源不动、目标不创建，仅打印 plan。
- 冲突：目标已存在时 skip 并记 conflict，源保留。
- 幂等：连跑 2 次，第 2 次无操作（所有项都命中 already-at-target 或直接无迁移计划）。

Helper 层直接调用 ``migrate_archive``，不跑真 CLI；tempdir 隔离并 monkey-patch
``_get_git_branch`` 固定 branch 为 ``main``。
"""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow import workflow_helpers  # noqa: E402
from harness_workflow.workflow_helpers import migrate_archive  # noqa: E402


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_legacy_requirement(root: Path, req_dir_name: str, branch: str = "main") -> Path:
    """在 legacy 下布置 ``.workflow/flow/archive/<branch>/requirements/<dir>/done-report.md``。"""
    src_dir = (
        root
        / ".workflow"
        / "flow"
        / "archive"
        / branch
        / "requirements"
        / req_dir_name
    )
    _write(src_dir / "done-report.md", f"# done report for {req_dir_name}\n")
    _write(src_dir / "changes" / "chg-01-x" / "change.md", "x\n")
    return src_dir


def _seed_legacy_bugfix(root: Path, bugfix_dir_name: str, branch: str = "main") -> Path:
    """在 legacy 下布置 ``.workflow/flow/archive/<branch>/bugfixes/<dir>/``。"""
    src_dir = (
        root
        / ".workflow"
        / "flow"
        / "archive"
        / branch
        / "bugfixes"
        / bugfix_dir_name
    )
    _write(src_dir / "bugfix.md", f"# bugfix for {bugfix_dir_name}\n")
    _write(src_dir / "test-evidence.md", "evidence\n")
    return src_dir


class MigrateArchiveHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        # 固定 branch=main，避免依赖真 git 仓库
        patcher = mock.patch.object(
            workflow_helpers,
            "_get_git_branch",
            return_value="main",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    # --- happy path ---

    def test_migrate_moves_requirement_archive_to_primary(self) -> None:
        src = _seed_legacy_requirement(self.root, "req-77-demo")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = migrate_archive(self.root, dry_run=False)

        self.assertEqual(rc, 0)
        dst = self.root / "artifacts" / "main" / "archive" / "requirements" / "req-77-demo"
        self.assertTrue(dst.exists(), "target requirement dir should exist after migrate")
        self.assertTrue((dst / "done-report.md").exists())
        self.assertTrue((dst / "changes" / "chg-01-x" / "change.md").exists())
        self.assertFalse(src.exists(), "legacy source dir should be removed")
        self.assertIn("1 migrated", buf.getvalue())

    def test_migrate_moves_bugfix_archive_to_primary(self) -> None:
        src = _seed_legacy_bugfix(self.root, "bugfix-9-demo")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = migrate_archive(self.root, dry_run=False)

        self.assertEqual(rc, 0)
        dst = self.root / "artifacts" / "main" / "archive" / "bugfixes" / "bugfix-9-demo"
        self.assertTrue(dst.exists())
        self.assertTrue((dst / "bugfix.md").exists())
        self.assertTrue((dst / "test-evidence.md").exists())
        self.assertFalse(src.exists())

    # --- dry-run ---

    def test_migrate_dry_run_does_not_move(self) -> None:
        src_req = _seed_legacy_requirement(self.root, "req-78-dryrun")
        src_bf = _seed_legacy_bugfix(self.root, "bugfix-10-dryrun")

        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = migrate_archive(self.root, dry_run=True)

        self.assertEqual(rc, 0)
        # 源仍在
        self.assertTrue(src_req.exists())
        self.assertTrue(src_bf.exists())
        # 目标根不创建（dry-run 应完全不动文件）
        dst_req_root = self.root / "artifacts" / "main" / "archive" / "requirements"
        dst_bf_root = self.root / "artifacts" / "main" / "archive" / "bugfixes"
        self.assertFalse(dst_req_root.exists())
        self.assertFalse(dst_bf_root.exists())
        out = buf.getvalue()
        self.assertIn("(dry-run)", out)
        self.assertIn("2 planned", out)

    # --- conflict ---

    def test_migrate_skips_conflict(self) -> None:
        src = _seed_legacy_requirement(self.root, "req-79-conflict")
        # 预先在 primary 放同名目录且内容不同
        pre_existing = (
            self.root
            / "artifacts"
            / "main"
            / "archive"
            / "requirements"
            / "req-79-conflict"
        )
        _write(pre_existing / "done-report.md", "# different content at target\n")

        buf_out = io.StringIO()
        buf_err = io.StringIO()
        with redirect_stdout(buf_out):
            old_stderr = sys.stderr
            sys.stderr = buf_err
            try:
                rc = migrate_archive(self.root, dry_run=False)
            finally:
                sys.stderr = old_stderr

        self.assertEqual(rc, 1, "rc must be non-zero on conflict")
        # 源保留
        self.assertTrue(src.exists())
        # 目标保持预置内容，不被覆盖
        self.assertEqual(
            (pre_existing / "done-report.md").read_text(encoding="utf-8"),
            "# different content at target\n",
        )
        self.assertIn("conflict", buf_err.getvalue())
        self.assertIn("1 skipped (conflict)", buf_out.getvalue())

    # --- idempotent ---

    def test_migrate_idempotent(self) -> None:
        _seed_legacy_requirement(self.root, "req-80-idem")
        _seed_legacy_bugfix(self.root, "bugfix-11-idem")

        # 第一次：真迁移
        buf1 = io.StringIO()
        with redirect_stdout(buf1):
            rc1 = migrate_archive(self.root, dry_run=False)
        self.assertEqual(rc1, 0)
        self.assertIn("2 migrated", buf1.getvalue())

        # 第二次：legacy 已空，应 no-op，rc=0
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = migrate_archive(self.root, dry_run=False)
        self.assertEqual(rc2, 0)
        self.assertIn("nothing to migrate", buf2.getvalue())

        # 目标保留
        self.assertTrue(
            (
                self.root
                / "artifacts"
                / "main"
                / "archive"
                / "requirements"
                / "req-80-idem"
            ).exists()
        )
        self.assertTrue(
            (
                self.root
                / "artifacts"
                / "main"
                / "archive"
                / "bugfixes"
                / "bugfix-11-idem"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
