"""对人文档落盘校验测试（req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-02（validate_human_docs 重写 + 精简废止项）/ req-41（废四类 brief）/ chg-03（validate_human_docs 重写删四类 brief））。

覆盖 ``src.harness_workflow.validate_human_docs.validate_human_docs`` 的核心行为：

- req-41+（精简扫描）：只校验 raw requirement.md + 交付总结.md；四类 brief 不再校验；
- req-39 / req-40（现行扫描）：req 级文档齐全 + chg-NN- 前缀文件命中时 items 全 ok；
- 缺少某份文档时，items 中该项为 missing；
- bugfix target 使用 bugfix 级清单，不列 change 级；
- 不存在的 target 抛 UnknownTargetError；
- 废止项（测试结论.md / 验收摘要.md）不再出现在任何报告中；
- req-02 ~ req-37 legacy 豁免：走 changes/ 子目录扫描，不报废止项 missing；
- CLI exit code 非零（缺失时），零（齐全时）。

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
    BRIEF_DEPRECATED_FROM_REQ_ID,
    BUGFIX_LEVEL_DOCS,
    CHANGE_LEVEL_DOCS,
    LEGACY_REQ_ID_CEILING,
    MIXED_TRANSITION_REQ_ID,
    REQ_LEVEL_DOCS,
    REQ_LEVEL_DOCS_SIMPLIFIED,
    STATUS_MALFORMED,
    STATUS_MISSING,
    STATUS_OK,
    UnknownTargetError,
    format_report,
    run_cli,
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

    def _make_req_flat(
        self,
        req_id: str = "req-99",
        slug: str = "demo",
        chg_ids: tuple[str, ...] = ("chg-01",),
    ) -> Path:
        """构造 req-39+ 风格的扁平目录（req 根目录下无 changes/ 子目录）。"""
        req_dir = self.root / "artifacts" / "main" / "requirements" / f"{req_id}-{slug}"
        req_dir.mkdir(parents=True)
        return req_dir

    def _make_req_legacy(
        self,
        req_id: str = "req-05",
        slug: str = "legacy",
        change_ids: tuple[str, ...] = ("chg-01-alpha",),
    ) -> Path:
        """构造 legacy 风格的目录（含 changes/ 子目录，对应 req-02 ~ req-37）。"""
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

    def _write_all_req_flat_docs(self, req_dir: Path, chg_ids: tuple[str, ...] = ("chg-01",)) -> None:
        """写齐新规扁平路径下的所有对人文档。"""
        for _stage, filename in REQ_LEVEL_DOCS:
            (req_dir / filename).write_text("stub", encoding="utf-8")
        for chg_id in chg_ids:
            for _stage, filename in CHANGE_LEVEL_DOCS:
                (req_dir / f"{chg_id}-{filename}").write_text("stub", encoding="utf-8")

    def _write_all_req_legacy_docs(self, req_dir: Path) -> None:
        """写齐 legacy changes/ 子目录风格的对人文档。"""
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

    # ---- tests（原有用例改写适配新常量）--------------------------------------

    def test_all_docs_present_returns_green(self) -> None:
        """新规 req-40（现行扫描，四类 brief 仍有效）：扁平路径全部文档齐全时全 ok。"""
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-40", slug="demo", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)
        kind, target_id, items = validate_human_docs(self.root, "req-40")
        self.assertEqual(kind, "req")
        self.assertEqual(target_id, "req-40-demo")
        # 2 req-level（需求摘要 + 交付总结）+ 2 change-level（变更简报 + 实施说明）= 4 条
        self.assertEqual(len(items), 4)
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK, msg=f"{item.filename} expected ok got {item.status}"
            )

    def test_missing_docs_reported(self) -> None:
        """新规 req-40（现行扫描）：缺 需求摘要.md 时报 missing。"""
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-40", slug="demo", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)
        # 故意删掉 需求摘要.md
        (req_dir / "需求摘要.md").unlink()
        _kind, _tid, items = validate_human_docs(self.root, "req-40")
        missing_items = [i for i in items if i.status == STATUS_MISSING]
        self.assertEqual(len(missing_items), 1)
        self.assertEqual(missing_items[0].filename, "需求摘要.md")
        self.assertEqual(missing_items[0].stage, "requirement_review")
        # 其他仍 ok
        ok_items = [i for i in items if i.status == STATUS_OK]
        self.assertEqual(len(ok_items), 3)

    def test_bugfix_target_uses_bugfix_doc_list(self) -> None:
        bugfix_dir = self._make_bugfix(bugfix_id="bugfix-7", slug="hotfix")
        self._write_all_bugfix_docs(bugfix_dir)
        kind, target_id, items = validate_human_docs(self.root, "bugfix-7")
        self.assertEqual(kind, "bugfix")
        self.assertEqual(target_id, "bugfix-7-hotfix")
        # 3 份 bugfix 级文档，不含 change-level 变更简报
        self.assertEqual(len(items), len(BUGFIX_LEVEL_DOCS))
        filenames = {i.filename for i in items}
        self.assertIn("回归简报.md", filenames)
        self.assertIn("交付总结.md", filenames)
        self.assertNotIn("变更简报.md", filenames)
        for item in items:
            self.assertEqual(item.status, STATUS_OK)

    def test_unknown_target_raises(self) -> None:
        self._make_req_flat(req_id="req-99", slug="demo")
        with self.assertRaises(UnknownTargetError):
            validate_human_docs(self.root, "req-404")

    def test_malformed_when_path_is_directory(self) -> None:
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-40", slug="demo", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)
        # 把 需求摘要.md 换成一个目录 → malformed（req-40 现行扫描仍校验需求摘要.md）
        (req_dir / "需求摘要.md").unlink()
        (req_dir / "需求摘要.md").mkdir()
        _kind, _tid, items = validate_human_docs(self.root, "req-40")
        malformed = [i for i in items if i.status == STATUS_MALFORMED]
        self.assertEqual(len(malformed), 1)
        self.assertEqual(malformed[0].filename, "需求摘要.md")

    def test_format_report_renders_icons(self) -> None:
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-40", slug="demo", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)
        # 删掉 交付总结.md 触发 missing 图标
        (req_dir / "交付总结.md").unlink()
        kind, tid, items = validate_human_docs(self.root, "req-40")
        text = format_report(kind, tid, items, stage="executing")
        self.assertIn("[✓]", text)
        self.assertIn("[ ]", text)
        self.assertIn("req-40-demo", text)
        self.assertIn("stage=executing", text)

    # ---- 新增用例（chg-02，AC-6 + AC-5）------------------------------------

    def test_validate_scans_flat_req_root(self) -> None:
        """AC-6（主）：新规 req-39 扁平目录命中 chg-NN- 前缀文件，changes/ 不存在不报错。"""
        req_dir = self._make_req_flat(req_id="req-39", slug="flat-demo")
        # 写 req 级
        (req_dir / "需求摘要.md").write_text("stub", encoding="utf-8")
        (req_dir / "交付总结.md").write_text("stub", encoding="utf-8")
        # 写 chg 级平铺文件
        (req_dir / "chg-01-变更简报.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-实施说明.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-02-变更简报.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-02-实施说明.md").write_text("stub", encoding="utf-8")
        # changes/ 子目录不存在
        self.assertFalse((req_dir / "changes").exists())

        kind, target_id, items = validate_human_docs(self.root, "req-39")
        self.assertEqual(kind, "req")
        # 2 req-level + 4 chg-level（chg-01 x2 + chg-02 x2）= 6 条
        self.assertEqual(len(items), 6)
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK,
                msg=f"{item.filename} expected ok got {item.status}"
            )
        filenames = {i.filename for i in items}
        self.assertIn("chg-01-变更简报.md", filenames)
        self.assertIn("chg-01-实施说明.md", filenames)
        self.assertIn("chg-02-变更简报.md", filenames)

    def test_validate_skips_legacy_req_before_38(self) -> None:
        """AC-6（豁免）：req-05（≤ req-37）走 legacy 扫描，废止项已删不报 missing。"""
        req_dir = self._make_req_legacy(req_id="req-05", slug="legacy", change_ids=("chg-01-alpha",))
        self._write_all_req_legacy_docs(req_dir)

        _kind, _tid, items = validate_human_docs(self.root, "req-05")
        filenames = [i.filename for i in items]
        # 废止项不应出现（testing/acceptance 已从常量删除）
        self.assertNotIn("测试结论.md", filenames)
        self.assertNotIn("验收摘要.md", filenames)
        # 核心对人文档应存在
        self.assertIn("需求摘要.md", filenames)
        # 所有扫到的 item 应为 ok（文档已写齐）
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK,
                msg=f"{item.filename} expected ok got {item.status}"
            )

    def test_validate_removed_testing_acceptance_docs(self) -> None:
        """AC-6（精简）：format_report 输出中不含 测试结论 / 验收摘要 字串（req-40 现行扫描）。"""
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-40", slug="demo", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)
        kind, target_id, items = validate_human_docs(self.root, "req-40")
        report = format_report(kind, target_id, items)
        self.assertNotIn("测试结论", report)
        self.assertNotIn("验收摘要", report)
        # 白名单内的文档名应出现
        self.assertIn("需求摘要.md", report)
        self.assertIn("交付总结.md", report)

    def test_validate_cli_exits_nonzero_on_missing(self) -> None:
        """AC-5（lint 行为）：缺 需求摘要.md 时 run_cli 返回 1（非零退出码）。"""
        # 构造 req-39 扁平目录，缺少 需求摘要.md
        req_dir = self._make_req_flat(req_id="req-39", slug="missing-test")
        # 只写 交付总结 + chg 级文件，不写 需求摘要.md
        (req_dir / "交付总结.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-变更简报.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-实施说明.md").write_text("stub", encoding="utf-8")

        exit_code = run_cli(self.root, "req-39")
        self.assertEqual(exit_code, 1, "缺失文档时 exit code 应为 1")

    def test_validate_cli_exits_zero_on_complete(self) -> None:
        """AC-5（lint 行为）：文档齐全时 run_cli 返回 0。"""
        chg_ids = ("chg-01",)
        req_dir = self._make_req_flat(req_id="req-39", slug="complete-test", chg_ids=chg_ids)
        self._write_all_req_flat_docs(req_dir, chg_ids=chg_ids)

        exit_code = run_cli(self.root, "req-39")
        self.assertEqual(exit_code, 0, "文档齐全时 exit code 应为 0")

    def test_legacy_ceiling_constant(self) -> None:
        """AC-11（部分）：LEGACY_REQ_ID_CEILING == 37，MIXED_TRANSITION_REQ_ID == 38（id 首次引用自证）。"""
        # LEGACY_REQ_ID_CEILING（req-37 legacy 豁免上界）
        self.assertEqual(LEGACY_REQ_ID_CEILING, 37)
        # MIXED_TRANSITION_REQ_ID（req-38 混合过渡期标识）
        self.assertEqual(MIXED_TRANSITION_REQ_ID, 38)

    # ---- req-41+ 精简扫描新增用例（chg-03，AC-08 / AC-09 / AC-06）-----------

    def test_brief_deprecated_constant(self) -> None:
        """AC-08（静态）：BRIEF_DEPRECATED_FROM_REQ_ID == 41；REQ_LEVEL_DOCS_SIMPLIFIED 只含 2 项。"""
        self.assertEqual(BRIEF_DEPRECATED_FROM_REQ_ID, 41)
        filenames = [fn for _, fn in REQ_LEVEL_DOCS_SIMPLIFIED]
        # 精简白名单：只有 requirement.md + 交付总结.md
        self.assertIn("requirement.md", filenames)
        self.assertIn("交付总结.md", filenames)
        self.assertEqual(len(filenames), 2)
        # 四类 brief 不在精简白名单
        self.assertNotIn("需求摘要.md", filenames)
        self.assertNotIn("变更简报.md", filenames)
        self.assertNotIn("实施说明.md", filenames)
        self.assertNotIn("回归简报.md", filenames)

    def test_validate_human_docs_brief_deprecated_req_41(self) -> None:
        """AC-09（主）：req-41 精简扫描 — 目录含 requirement.md + 交付总结.md，断言 items=2、全 ok、exit 0。"""
        req_dir = self._make_req_flat(req_id="req-41", slug="smoke")
        (req_dir / "requirement.md").write_text("stub raw requirement", encoding="utf-8")
        (req_dir / "交付总结.md").write_text("stub delivery summary", encoding="utf-8")

        kind, target_id, items = validate_human_docs(self.root, "req-41")
        self.assertEqual(kind, "req")
        self.assertEqual(target_id, "req-41-smoke")
        # 精简扫描：只有 requirement.md + 交付总结.md 两条
        self.assertEqual(len(items), 2, msg=f"expected 2 items, got {len(items)}: {[i.filename for i in items]}")
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK,
                msg=f"{item.filename} expected ok got {item.status}"
            )
        # exit code
        exit_code = run_cli(self.root, "req-41")
        self.assertEqual(exit_code, 0)

    def test_validate_human_docs_req_41_missing_delivery_summary(self) -> None:
        """AC-09（缺交付总结）：req-41 目录只放 requirement.md，缺 交付总结.md → exit != 0 + status missing。"""
        req_dir = self._make_req_flat(req_id="req-41", slug="missing-summary")
        (req_dir / "requirement.md").write_text("stub", encoding="utf-8")
        # 故意不写 交付总结.md

        _kind, _tid, items = validate_human_docs(self.root, "req-41")
        self.assertEqual(len(items), 2)
        missing_items = [i for i in items if i.status == STATUS_MISSING]
        self.assertEqual(len(missing_items), 1)
        self.assertEqual(missing_items[0].filename, "交付总结.md")
        self.assertEqual(missing_items[0].stage, "done")

        exit_code = run_cli(self.root, "req-41")
        self.assertNotEqual(exit_code, 0, "缺交付总结.md 时 exit code 应非零")

    def test_validate_human_docs_req_41_ignores_brief_stubs(self) -> None:
        """AC-09（静默忽略）：req-41 目录额外放 chg-01-变更简报.md（空壳），validate 静默忽略（不报额外错）。"""
        req_dir = self._make_req_flat(req_id="req-41", slug="with-stubs")
        (req_dir / "requirement.md").write_text("stub", encoding="utf-8")
        (req_dir / "交付总结.md").write_text("stub", encoding="utf-8")
        # 额外放 brief 空壳（CLI 历史自动生成的残留）
        (req_dir / "chg-01-变更简报.md").write_text("", encoding="utf-8")
        (req_dir / "chg-01-实施说明.md").write_text("", encoding="utf-8")
        (req_dir / "reg-01-回归简报.md").write_text("", encoding="utf-8")
        (req_dir / "需求摘要.md").write_text("", encoding="utf-8")

        _kind, _tid, items = validate_human_docs(self.root, "req-41")
        # 精简扫描：只有 requirement.md + 交付总结.md 两条，空壳 brief 静默忽略
        self.assertEqual(
            len(items), 2,
            msg=f"expected 2 items (brief stubs silently ignored), got {len(items)}: {[i.filename for i in items]}"
        )
        for item in items:
            self.assertEqual(item.status, STATUS_OK)

        exit_code = run_cli(self.root, "req-41")
        self.assertEqual(exit_code, 0, "brief 空壳不影响 exit code（精简扫描静默忽略）")

    def test_validate_human_docs_req_39_unchanged(self) -> None:
        """AC-06（回归）：req-39 仍按现行扫描（四类 brief 全查），行为不变。"""
        req_dir = self._make_req_flat(req_id="req-39", slug="regression-guard")
        # req-39 现行扫描：需求摘要 + 交付总结 + chg 级 brief
        (req_dir / "需求摘要.md").write_text("stub", encoding="utf-8")
        (req_dir / "交付总结.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-变更简报.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-实施说明.md").write_text("stub", encoding="utf-8")

        _kind, _tid, items = validate_human_docs(self.root, "req-39")
        # 2 req-level + 2 chg-level = 4 条
        self.assertEqual(len(items), 4, msg=f"req-39 should have 4 items, got {len(items)}: {[i.filename for i in items]}")
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK,
                msg=f"{item.filename} expected ok got {item.status}"
            )
        # 现行扫描：需求摘要.md 仍在期望集合内
        filenames = {i.filename for i in items}
        self.assertIn("需求摘要.md", filenames)
        self.assertIn("交付总结.md", filenames)
        self.assertIn("chg-01-变更简报.md", filenames)
        self.assertIn("chg-01-实施说明.md", filenames)

    def test_validate_human_docs_req_38_legacy(self) -> None:
        """AC-06（回归）：req-38 走 mixed 双轨扫描（legacy 行为），不走精简扫描。"""
        req_dir = self._make_req_legacy(req_id="req-38", slug="mixed-legacy", change_ids=("chg-01-alpha",))
        # 写 req-38 现行 legacy/mixed 文档
        (req_dir / "需求摘要.md").write_text("stub", encoding="utf-8")
        (req_dir / "交付总结.md").write_text("stub", encoding="utf-8")
        # 写 changes/ 子目录内的文档
        change_dir = req_dir / "changes" / "chg-01-alpha"
        (change_dir / "变更简报.md").write_text("stub", encoding="utf-8")
        (change_dir / "实施说明.md").write_text("stub", encoding="utf-8")

        _kind, _tid, items = validate_human_docs(self.root, "req-38")
        # req-38 mixed：2 req-level + chg 级（变更简报 + 实施说明）= ≥ 2 条（有 changes/ 时含 chg 级）
        self.assertGreaterEqual(len(items), 2)
        filenames = {i.filename for i in items}
        # req 级仍在期望集合（mixed 扫描不走精简分支）
        self.assertIn("需求摘要.md", filenames)
        self.assertIn("交付总结.md", filenames)
        # 不走精简分支：requirement.md 不在期望集合（精简扫描专属）
        self.assertNotIn("requirement.md", filenames)
        for item in items:
            self.assertEqual(
                item.status, STATUS_OK,
                msg=f"{item.filename} expected ok got {item.status}"
            )

    def test_req_level_docs_no_deprecated_items(self) -> None:
        """AC-6（静态断言）：REQ_LEVEL_DOCS 不含废止的 测试结论.md / 验收摘要.md。"""
        filenames = [fn for _, fn in REQ_LEVEL_DOCS]
        self.assertNotIn("测试结论.md", filenames)
        self.assertNotIn("验收摘要.md", filenames)

    def test_bugfix_level_docs_no_deprecated_items(self) -> None:
        """AC-6（静态断言）：BUGFIX_LEVEL_DOCS 不含废止的 测试结论.md / 验收摘要.md。"""
        filenames = [fn for _, fn in BUGFIX_LEVEL_DOCS]
        self.assertNotIn("测试结论.md", filenames)
        self.assertNotIn("验收摘要.md", filenames)


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
        """AC-5（CLI 串联）：旧路径 legacy req-28，缺文档时 subprocess exit code = 1。"""
        # 构造只有 需求摘要.md 的 req-28（≤ LEGACY_REQ_ID_CEILING，走 legacy 路径）
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
