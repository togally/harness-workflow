"""chg-B polish 测试套件
chg-D（精简命令体系）更新：[ASSISTANT INSTRUCTION] 提示句移到 playbook-refresh 触发，
init_playbook 不再输出提示。
chg-F：--no-llm flag 已删除；NoopProvider fallback 自然触发提示句。

TC-01  playbook_refresh 在路书已存在 + LLM 区段仍 TODO + NoopProvider 时输出提示句（chg-D/chg-F 行为）
TC-01b init_playbook 在路书已存在时不输出 [ASSISTANT INSTRUCTION]（chg-D 验证）
TC-02  K-01 命中 >= 3 个时折叠输出（一行 + 命中清单）
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class RefreshPlaybookPolish1Test(unittest.TestCase):
    """TC-01 (chg-D/chg-F): playbook_refresh 在路书已存在 + LLM 区段仍 TODO + NoopProvider 时输出提示句。
    TC-01b: init_playbook 在路书已存在时不输出 [ASSISTANT INSTRUCTION]（chg-D 行为）。
    """

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-polish1-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_hint_printed_by_refresh_when_playbook_exists_with_todo(self) -> None:
        """TC-01 (chg-D/chg-F): 路书已存在 + 仍有 <!-- TODO: 占位 + NoopProvider → 应输出 LLM 提示句。"""
        from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
        from harness_workflow.playbook.llm import NoopProvider
        playbook_dir = self.repo / PLAYBOOK_ROOT_SUFFIX
        playbook_dir.mkdir(parents=True, exist_ok=True)

        # 写入含 <!-- TODO: 占位的文件（模拟 NoopProvider fallback 后未填充的状态）
        (playbook_dir / "overview.md").write_text(
            "# Overview\n"
            "<!-- AUTO:DOMAIN_LIST -->\n"
            "<!-- /AUTO:DOMAIN_LIST -->\n"
            "<!-- LLM:OVERVIEW_DESC -->\n"
            "<!-- TODO: 请填写项目概述 -->\n"
            "<!-- /LLM:OVERVIEW_DESC -->\n",
            encoding="utf-8",
        )
        # architecture.md 需存在（AUTO:STACK 等）
        (playbook_dir / "architecture.md").write_text(
            "# Architecture\n"
            "<!-- AUTO:STACK -->\n"
            "<!-- /AUTO:STACK -->\n"
            "<!-- AUTO:SCRIPTS -->\n"
            "<!-- /AUTO:SCRIPTS -->\n"
            "<!-- AUTO:LAYOUT -->\n"
            "<!-- /AUTO:LAYOUT -->\n",
            encoding="utf-8",
        )
        (playbook_dir / "code-map.md").write_text(
            "# Code Map\n"
            "<!-- AUTO:DOMAIN_FILES -->\n"
            "<!-- /AUTO:DOMAIN_FILES -->\n",
            encoding="utf-8",
        )

        import os
        noop = NoopProvider()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with mock.patch("harness_workflow.playbook.llm.auto_detect_provider", return_value=noop):
                os.environ.pop("CI", None)
                from harness_workflow.tools.harness_playbook_refresh import playbook_refresh
                rc = playbook_refresh(self.repo)
        output = buf.getvalue()

        self.assertEqual(rc, 0)
        self.assertIn(
            "[ASSISTANT INSTRUCTION",
            output,
            msg="refresh + NoopProvider 在路书含 TODO 占位时应输出 LLM 填充强指令提示",
        )

    def test_init_playbook_no_hint_when_playbook_exists(self) -> None:
        """TC-01b (chg-D): init_playbook 在路书已存在时不输出 [ASSISTANT INSTRUCTION]。"""
        from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
        playbook_dir = self.repo / PLAYBOOK_ROOT_SUFFIX
        playbook_dir.mkdir(parents=True, exist_ok=True)

        # 写入含 <!-- TODO: 占位的文件
        (playbook_dir / "overview.md").write_text(
            "# Overview\n"
            "<!-- LLM:OVERVIEW_DESC -->\n"
            "<!-- TODO: 请填写项目概述 -->\n"
            "<!-- /LLM:OVERVIEW_DESC -->\n",
            encoding="utf-8",
        )

        import os
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            with mock.patch.dict(os.environ, {"CI": "true"}):
                from harness_workflow.playbook.init import init_playbook
                rc = init_playbook(self.repo)
        output = buf.getvalue()

        self.assertEqual(rc, 0)
        self.assertIn(
            "playbook 已存在，跳过初始化",
            output,
            msg="应打印 '已存在' 提示",
        )
        # chg-D: init_playbook 不再输出提示句
        self.assertNotIn(
            "[ASSISTANT INSTRUCTION",
            output,
            msg="chg-D: init_playbook 不应输出 [ASSISTANT INSTRUCTION]，请用 harness playbook-refresh",
        )


class PlaybookCheckK01FoldingTest(unittest.TestCase):
    """TC-02: K-01 命中 >= 3 个时折叠输出。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-polish2-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _make_domain_readme(self, domain_name: str, with_todo: bool = True) -> None:
        """在 artifacts/project/playbooks/domains/{domain}/README.md 创建测试文件。"""
        domain_dir = (
            self.repo / "artifacts" / "project" / "playbooks" / "domains" / domain_name
        )
        domain_dir.mkdir(parents=True, exist_ok=True)
        if with_todo:
            content = (
                f"# {domain_name}\n\n"
                "## 职责描述\n"
                "<!-- TODO: 请填写职责描述 -->\n\n"
            )
        else:
            content = (
                f"# {domain_name}\n\n"
                "## 职责描述\n"
                f"{domain_name} 模块负责处理相关业务逻辑。\n\n"
            )
        (domain_dir / "README.md").write_text(content, encoding="utf-8")

    def test_k01_folded_when_3_or_more_hits(self) -> None:
        """K-01 命中 3 个以上时，输出折叠为一行（含命中数 + 前 5 domain）。"""
        # 创建 4 个 domain，都有 TODO 占位
        for d in ["payment", "user", "order", "product"]:
            self._make_domain_readme(d, with_todo=True)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            from harness_workflow.tools.harness_playbook_check import playbook_check
            rc = playbook_check(self.repo)
        output = buf.getvalue()

        # exit code 0（K-01 不阻断）
        self.assertEqual(rc, 0, msg=f"K-01 alone should not cause exit 1. output={output!r}")
        # 折叠输出包含命中数
        self.assertIn(
            "empty keywords (K-01):",
            output,
            msg="应有 K-01 折叠输出行",
        )
        # 折叠行应含 domain 数
        self.assertIn("4 domains", output, msg="折叠行应含命中数（4 domains）")
        # 不应逐条列出（因为 >= 3 条应折叠）
        k01_lines = [line for line in output.splitlines() if "KEYWORD_COVERAGE" in line]
        self.assertEqual(
            len(k01_lines),
            0,
            msg=f"K-01 >= 3 时不应逐条列出 KEYWORD_COVERAGE，但实际有 {len(k01_lines)} 行：{k01_lines}",
        )

    def test_k01_listed_when_2_or_fewer_hits(self) -> None:
        """K-01 命中 <= 2 个时，逐条列出（保持现状）。"""
        # 创建 2 个 domain，都有 TODO 占位
        for d in ["payment", "user"]:
            self._make_domain_readme(d, with_todo=True)

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            from harness_workflow.tools.harness_playbook_check import playbook_check
            rc = playbook_check(self.repo)
        output = buf.getvalue()

        # exit code 0（K-01 不阻断）
        self.assertEqual(rc, 0, msg=f"K-01 alone should not cause exit 1. output={output!r}")
        # 应逐条列出（<= 2 保持现状）
        k01_domain_lines = [line for line in output.splitlines()
                            if "empty keywords (K-01):" in line and "domains" not in line]
        self.assertGreaterEqual(
            len(k01_domain_lines),
            1,
            msg=f"K-01 <= 2 时应逐条列出，但无单独行。output={output!r}",
        )


if __name__ == "__main__":
    unittest.main()
