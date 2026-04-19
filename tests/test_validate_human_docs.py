"""对人文档落盘校验测试（req-28 / chg-05，AC-09）。

覆盖 ``src.harness_workflow.validate_human_docs.validate_human_docs`` 的核心行为：

- req 级全部对人文档齐全时，items 全 ok；
- 缺少某份文档时，items 中该项为 missing；
- bugfix target 使用 bugfix 级清单，不列 change 级；
- 不存在的 target 抛 UnknownTargetError。

硬约束：使用 tempdir 隔离，严禁污染主仓 runtime / artifacts。
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.validate_human_docs import (  # noqa: E402
    BUGFIX_LEVEL_DOCS,
    CHANGE_LEVEL_DOCS,
    REQ_LEVEL_DOCS,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_OK,
    UnknownTargetError,
    format_report,
    validate_human_docs,
)


class ValidateHumanDocsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-validate-human-docs-"))
        self.root = self.tempdir / "repo"
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    # ---- helpers ----------------------------------------------------------

    def _make_req(
        self,
        req_id: str = "req-99",
        slug: str = "demo",
        change_ids: tuple[str, ...] = ("chg-01-alpha",),
    ) -> Path:
        """在 tempdir 里构造 artifacts/main/requirements/{req-id}-{slug}/ 结构。"""
        req_dir = self.root / "artifacts" / "main" / "requirements" / f"{req_id}-{slug}"
        req_dir.mkdir(parents=True)
        for chg in change_ids:
            (req_dir / "changes" / chg).mkdir(parents=True)
        return req_dir

    def _make_bugfix(self, bugfix_id: str = "bugfix-7", slug: str = "hotfix") -> Path:
        bugfix_dir = (
            self.root / "artifacts" / "main" / "bugfixes" / f"{bugfix_id}-{slug}"
        )
        bugfix_dir.mkdir(parents=True)
        return bugfix_dir

    def _write_all_req_docs(self, req_dir: Path) -> None:
        for _stage, filename in REQ_LEVEL_DOCS:
            (req_dir / filename).write_text("stub", encoding="utf-8")
        changes_dir = req_dir / "changes"
        if changes_dir.exists():
            for change_path in changes_dir.iterdir():
                if change_path.is_dir():
                    for _stage, filename in CHANGE_LEVEL_DOCS:
                        (change_path / filename).write_text("stub", encoding="utf-8")

    def _write_all_bugfix_docs(self, bugfix_dir: Path) -> None:
        for _stage, filename in BUGFIX_LEVEL_DOCS:
            (bugfix_dir / filename).write_text("stub", encoding="utf-8")

    # ---- tests ------------------------------------------------------------

    def test_all_docs_present_returns_green(self) -> None:
        self._make_req(req_id="req-99", slug="demo", change_ids=("chg-01-alpha",))
        self._write_all_req_docs(
            self.root / "artifacts" / "main" / "requirements" / "req-99-demo"
        )
        kind, target_id, items = validate_human_docs(self.root, "req-99")
        self.assertEqual(kind, "req")
        self.assertEqual(target_id, "req-99-demo")
        # 4 req-level + 2 change-level = 6 条
        self.assertEqual(len(items), 6)
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK, msg=f"{item.filename} expected ok got {item.status}"
            )

    def test_missing_docs_reported(self) -> None:
        req_dir = self._make_req(
            req_id="req-99", slug="demo", change_ids=("chg-01-alpha",)
        )
        self._write_all_req_docs(req_dir)
        # 故意删掉 需求摘要.md
        (req_dir / "需求摘要.md").unlink()
        _kind, _tid, items = validate_human_docs(self.root, "req-99")
        missing_items = [i for i in items if i.status == STATUS_MISSING]
        self.assertEqual(len(missing_items), 1)
        self.assertEqual(missing_items[0].filename, "需求摘要.md")
        self.assertEqual(missing_items[0].stage, "requirement_review")
        # 其他仍 ok
        ok_items = [i for i in items if i.status == STATUS_OK]
        self.assertEqual(len(ok_items), 5)

    def test_bugfix_target_uses_bugfix_doc_list(self) -> None:
        bugfix_dir = self._make_bugfix(bugfix_id="bugfix-7", slug="hotfix")
        self._write_all_bugfix_docs(bugfix_dir)
        kind, target_id, items = validate_human_docs(self.root, "bugfix-7")
        self.assertEqual(kind, "bugfix")
        self.assertEqual(target_id, "bugfix-7-hotfix")
        # 5 份 bugfix 级文档，不含 change-level
        self.assertEqual(len(items), len(BUGFIX_LEVEL_DOCS))
        filenames = {i.filename for i in items}
        self.assertIn("回归简报.md", filenames)
        self.assertIn("交付总结.md", filenames)
        self.assertNotIn("变更简报.md", filenames)
        for item in items:
            self.assertEqual(item.status, STATUS_OK)

    def test_unknown_target_raises(self) -> None:
        self._make_req(req_id="req-99", slug="demo")
        with self.assertRaises(UnknownTargetError):
            validate_human_docs(self.root, "req-404")

    def test_malformed_when_path_is_directory(self) -> None:
        req_dir = self._make_req(
            req_id="req-99", slug="demo", change_ids=("chg-01-alpha",)
        )
        self._write_all_req_docs(req_dir)
        # 把 需求摘要.md 换成一个目录 → malformed
        (req_dir / "需求摘要.md").unlink()
        (req_dir / "需求摘要.md").mkdir()
        _kind, _tid, items = validate_human_docs(self.root, "req-99")
        malformed = [i for i in items if i.status == STATUS_MALFORMED]
        self.assertEqual(len(malformed), 1)
        self.assertEqual(malformed[0].filename, "需求摘要.md")

    def test_format_report_renders_icons(self) -> None:
        req_dir = self._make_req(
            req_id="req-99", slug="demo", change_ids=("chg-01-alpha",)
        )
        self._write_all_req_docs(req_dir)
        (req_dir / "测试结论.md").unlink()
        kind, tid, items = validate_human_docs(self.root, "req-99")
        text = format_report(kind, tid, items, stage="executing")
        self.assertIn("[✓]", text)
        self.assertIn("[ ]", text)
        self.assertIn("req-99-demo", text)
        self.assertIn("stage=executing", text)


class ValidateHumanDocsCliTest(unittest.TestCase):
    """通过子进程调用 ``python -m harness_workflow validate --human-docs`` 验证 CLI 串起来。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-validate-cli-"))
        self.root = self.tempdir / "repo"
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _run_cli(self, *args: str):
        import os
        import subprocess

        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "harness_workflow", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(self.tempdir),
            env=env,
        )

    def test_cli_exits_nonzero_on_missing_docs(self) -> None:
        # 构造只有 需求摘要.md 的 req-28（模拟 briefing 示例）
        req_dir = (
            self.root
            / "artifacts"
            / "main"
            / "requirements"
            / "req-28-demo"
        )
        (req_dir / "changes" / "chg-01-alpha").mkdir(parents=True)
        (req_dir / "需求摘要.md").write_text("stub", encoding="utf-8")

        result = self._run_cli(
            "validate",
            "--root",
            str(self.root),
            "--human-docs",
            "--requirement",
            "req-28",
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("[✓]", result.stdout)
        self.assertIn("[ ]", result.stdout)
        self.assertIn("需求摘要.md", result.stdout)

    def test_cli_mutual_exclusion(self) -> None:
        result = self._run_cli(
            "validate",
            "--root",
            str(self.root),
            "--human-docs",
            "--requirement",
            "req-1",
            "--bugfix",
            "bugfix-1",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("互斥", result.stdout)


if __name__ == "__main__":
    unittest.main()
