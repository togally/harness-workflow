"""chg-B polish 测试套件

TC-01  init_playbook 在路书已存在 + LLM 区段仍 TODO 时仍输出提示句
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


class InitPlaybookPolish1Test(unittest.TestCase):
    """TC-01: init_playbook 在路书已存在 + LLM 区段仍 TODO 时仍输出提示句。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-polish1-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_hint_printed_when_playbook_exists_with_todo(self) -> None:
        """路书已存在 + 仍有 <!-- TODO: 占位 → 应输出 LLM 提示句。"""
        from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
        playbook_dir = self.repo / PLAYBOOK_ROOT_SUFFIX
        playbook_dir.mkdir(parents=True, exist_ok=True)

        # 写入含 <!-- TODO: 占位的文件（模拟 --no-llm 后未填充的状态）
        (playbook_dir / "overview.md").write_text(
            "# Overview\n"
            "<!-- LLM:OVERVIEW_DESC -->\n"
            "<!-- TODO: 请填写项目概述 -->\n"
            "<!-- /LLM:OVERVIEW_DESC -->\n",
            encoding="utf-8",
        )

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            from harness_workflow.playbook.init import init_playbook
            rc = init_playbook(self.repo, no_llm=True)
        output = buf.getvalue()

        self.assertEqual(rc, 0)
        self.assertIn(
            "playbook 已存在，跳过初始化",
            output,
            msg="应打印 '已存在' 提示",
        )
        self.assertIn(
            "[ASSISTANT INSTRUCTION",
            output,
            msg="路书已存在但含 TODO 占位时，应仍输出 LLM 填充强指令提示",
        )

    def test_no_hint_when_playbook_exists_without_todo(self) -> None:
        """路书已存在且无 <!-- TODO: 占位 → 不应输出 LLM 提示句。"""
        from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX
        playbook_dir = self.repo / PLAYBOOK_ROOT_SUFFIX
        playbook_dir.mkdir(parents=True, exist_ok=True)

        # 写入无 TODO 占位的文件（模拟已填充状态）
        (playbook_dir / "overview.md").write_text(
            "# Overview\n"
            "<!-- LLM:OVERVIEW_DESC -->\n"
            "这是一个已填写完毕的项目概述。\n"
            "<!-- /LLM:OVERVIEW_DESC -->\n",
            encoding="utf-8",
        )

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            from harness_workflow.playbook.init import init_playbook
            rc = init_playbook(self.repo, no_llm=True)
        output = buf.getvalue()

        self.assertEqual(rc, 0)
        self.assertIn("playbook 已存在，跳过初始化", output)
        self.assertNotIn(
            "LLM 区段未填充",
            output,
            msg="路书已存在且无 TODO 占位时，不应输出 LLM 填充提示句",
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
