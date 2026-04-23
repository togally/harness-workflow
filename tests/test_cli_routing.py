"""chg-07（CLI 路由修正：harness install 接 install_repo + 移除 harness update --flag 的 install_repo hack）

来源：req-36（harness install 同步契约完整性修复（存量项目 .workflow/ 与 scaffold_v2
mirror 保持一致））/ reg-02（req-36 AC-5 收口：CLI 路由 + packaging 双根因）根因 A。

设计：subprocess 黑盒 + stdout/stderr 模式断言 + 文件副作用代理（install_repo 跑过
必打印 "Update summary"，--check 模式下额外打印 "No files were changed."；--force-managed
会覆盖用户篡改的 managed 文件）。不直接 spy，但通过副作用证明路由生效。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class CliRoutingTest(unittest.TestCase):
    """harness install 接 install_repo + harness update --flag 硬 fail 的路由契约测试。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-cli-routing-"))
        self.repo = self.tempdir / "repo"
        self.repo.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "harness_workflow", *args],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

    # ----- install 路径 4 个用例 -----

    def test_install_with_agent_invokes_install_repo(self) -> None:
        """harness install --agent kimi 必须调用 install_repo（stdout 含 "Update summary"）。

        当前状态（chg-07 STEP-1 红）：cli.py:387 install 子命令只调 _run_tool_script
        ("harness_install.py", ["--agent", agent], root) → tools/harness_install.py
        只调 install_agent，不调 install_repo → 不输出 "Update summary"。
        STEP-2 绿：tools/harness_install.py main() 末尾追加 install_repo(root) 调用。
        """
        result = self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn(
            "Update summary",
            result.stdout,
            msg=f"install_repo 未被调用（stdout 无 'Update summary'）。stdout={result.stdout!r}\nstderr={result.stderr!r}",
        )

    def test_install_check_passes_check_kwarg_to_install_repo(self) -> None:
        """harness install --check 必须透传 check=True（dry-run，不写文件 + 打印 "No files were changed."）。"""
        # 先做一次正常 install 让仓库进入 managed 态
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        # 篡改一个 mirror 文件让 dry-run 能看到 drift（context/index.md 是 mirror 内容）
        index_md = self.repo / ".workflow" / "context" / "index.md"
        if index_md.exists():
            original = index_md.read_text(encoding="utf-8")
            index_md.write_text("# tampered for dry-run\n", encoding="utf-8")
        try:
            # --check 必须以 check=True 调 install_repo（不写文件 + 输出 "No files were changed."）
            result = self.run_cli(
                "install", "--root", str(self.repo), "--agent", "kimi", "--check"
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertIn("Update summary", result.stdout)
            self.assertIn(
                "No files were changed",
                result.stdout,
                msg=f"--check 未透传 check=True（stdout 无 'No files were changed.'）。stdout={result.stdout!r}",
            )
            # 篡改未被覆盖（dry-run 不写文件）
            if index_md.exists():
                self.assertEqual(
                    index_md.read_text(encoding="utf-8"),
                    "# tampered for dry-run\n",
                    msg="dry-run 模式不应写文件，但 index.md 被覆盖",
                )
        finally:
            if index_md.exists() and 'original' in dir():
                pass  # tearDown 会清

    def test_install_force_managed_passes_kwarg_to_install_repo(self) -> None:
        """harness install --force-managed 必须透传 force_managed=True（覆盖用户篡改的 managed 文件）。"""
        # 先做一次正常 install
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        # 篡改 managed 文件 context/index.md
        index_md = self.repo / ".workflow" / "context" / "index.md"
        self.assertTrue(index_md.exists(), msg="预置失败：index.md 应存在")
        index_md.write_text("# tampered\n", encoding="utf-8")
        # 不带 --force-managed：should skip user-modified（不覆盖）
        result_no_force = self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        self.assertEqual(result_no_force.returncode, 0, msg=result_no_force.stderr or result_no_force.stdout)
        self.assertEqual(
            index_md.read_text(encoding="utf-8"),
            "# tampered\n",
            msg="无 --force-managed 时不应覆盖用户篡改",
        )
        # 带 --force-managed：should overwrite
        result_force = self.run_cli(
            "install", "--root", str(self.repo), "--agent", "kimi", "--force-managed"
        )
        self.assertEqual(result_force.returncode, 0, msg=result_force.stderr or result_force.stdout)
        self.assertNotEqual(
            index_md.read_text(encoding="utf-8"),
            "# tampered\n",
            msg="--force-managed 未透传 force_managed=True，篡改未被覆盖",
        )

    def test_install_all_platforms_passes_kwarg_to_install_repo(self) -> None:
        """harness install --all-platforms 必须透传 force_all_platforms=True（不被 active_agent 收敛）。"""
        # 先 install kimi 和 claude，让两个 platform 都进入 managed
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        self.run_cli("install", "--root", str(self.repo), "--agent", "claude")
        # 篡改 claude 的 managed 文件
        claude_skill = self.repo / ".claude" / "skills" / "harness" / "SKILL.md"
        self.assertTrue(claude_skill.exists(), msg="预置失败：claude skill 应存在")
        claude_skill.write_text("# tampered claude skill\n", encoding="utf-8")
        # active_agent 是 claude（最后 install 的），跑 --all-platforms 必须不被收敛
        result = self.run_cli(
            "install", "--root", str(self.repo), "--agent", "kimi",
            "--all-platforms", "--force-managed"
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        # claude skill 应该被覆盖（--all-platforms 让 claude 也在 scope 内 + --force-managed 覆盖）
        self.assertNotIn(
            "tampered",
            claude_skill.read_text(encoding="utf-8"),
            msg="--all-platforms 未透传 force_all_platforms=True，claude 篡改未被覆盖",
        )

    # ----- update 路径 3 类用例 -----

    def test_update_with_check_flag_hard_fails_with_migration_hint(self) -> None:
        """harness update --check 必须硬 fail（exit 1）+ stderr 含迁移提示。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo), "--check")
        self.assertEqual(
            result.returncode, 1,
            msg=f"--check 应硬 fail（exit 1），实际 rc={result.returncode}\nstdout={result.stdout!r}\nstderr={result.stderr!r}",
        )
        self.assertIn(
            "harness install --check",
            result.stderr,
            msg=f"stderr 未含迁移提示。stderr={result.stderr!r}",
        )
        # 不应再走 install_repo drift preview
        self.assertNotIn("Update summary", result.stdout)

    def test_update_with_force_managed_flag_hard_fails_with_migration_hint(self) -> None:
        """harness update --force-managed 必须硬 fail（exit 1）+ stderr 含迁移提示。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo), "--force-managed")
        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertIn("harness install --force-managed", result.stderr)
        self.assertNotIn("Update summary", result.stdout)

    def test_update_with_all_platforms_flag_hard_fails_with_migration_hint(self) -> None:
        """harness update --all-platforms 必须硬 fail（exit 1）+ stderr 含迁移提示。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo), "--all-platforms")
        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertIn("harness install --all-platforms", result.stderr)
        self.assertNotIn("Update summary", result.stdout)

    def test_update_with_agent_flag_hard_fails_with_migration_hint(self) -> None:
        """harness update --agent kimi 必须硬 fail（exit 1）+ stderr 含迁移提示。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo), "--agent", "kimi")
        self.assertEqual(result.returncode, 1, msg=result.stderr or result.stdout)
        self.assertIn("harness install --agent", result.stderr)
        self.assertNotIn("Update summary", result.stdout)

    # ----- update 路径保留分支 -----

    def test_update_bare_still_prints_role_contract_guidance(self) -> None:
        """裸 harness update（无任何 flag）仍打印 req-33 / chg-02 三行引导 + exit 0。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo))
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("harness update 已重定义为角色契约触发", result.stdout)
        self.assertIn("生成项目现状报告", result.stdout)
        self.assertIn("harness install", result.stdout)

    def test_update_scan_still_routes_to_scan_project(self) -> None:
        """harness update --scan 仍调 scan_project（保留分支，与 install_repo 无关）。"""
        self.run_cli("install", "--root", str(self.repo), "--agent", "kimi")
        result = self.run_cli("update", "--root", str(self.repo), "--scan")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("项目适配报告", result.stdout)


if __name__ == "__main__":
    unittest.main()
