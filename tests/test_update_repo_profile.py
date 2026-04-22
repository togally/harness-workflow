"""Tests for req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/
chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）。

覆盖 AC-02（hash 漂移三态）+ AC-05（用户自定义保护回归守护）：
- test_update_generates_profile_first_run：首次 update → profile 落盘 +
  stderr 含 "初始 hash"。
- test_update_profile_hash_stable_on_second_run：连续两次 update，项目描述
  未变 → stderr 不含 "漂移"。
- test_update_profile_drift_on_pyproject_change：第二次前改 pyproject.toml 的
  package_name → stderr 含 "hash 漂移：<old>→<new>"。
- test_update_skips_user_authored_claude_md：tmp 仓先种带自定义内容的 CLAUDE.md →
  update_repo 不覆盖 + stderr 含 "skipping user-authored file CLAUDE.md"（回归
  守护 req-31 / chg-03 / sug-14，chg-02 不扩展该判据，仅验证其在 profile
  接入后依然生效）。
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# req-32 / chg-02 / Step 1：渲染 profile 路径常量，测试用例断言落盘位置
PROFILE_REL = Path(".workflow") / "context" / "project-profile.md"


def _seed_minimal_repo(root: Path) -> None:
    """构造 update_repo 可运行的最小 harness workspace。

    - .workflow/state/platforms.yaml: active_agent=codex（决定 install_local_skills 走 codex 分支）
    - .codex/harness/config.json: language 默认
    - pyproject.toml: 提供 scanner 可识别的 python 项目描述，保证 profile 有内容
    """
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".workflow" / "state" / "platforms.yaml").write_text(
        "active_agent: codex\n",
        encoding="utf-8",
    )
    # pyproject.toml：scanner 静态解析入口，保证 content_hash 非空
    (root / "pyproject.toml").write_text(
        """
[project]
name = "sample-pkg"
dependencies = ["pyyaml>=6.0"]
""".lstrip(),
        encoding="utf-8",
    )


def _run_update(root: Path) -> tuple[int, str, str]:
    """调用 update_repo 并捕获 stdout/stderr，返回 (rc, stdout, stderr)。"""
    from harness_workflow.workflow_helpers import update_repo

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = update_repo(root, check=False)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


class UpdateRepoProfileIntegrationTest(unittest.TestCase):
    """chg-02：update_repo 末尾 profile 写盘 + hash 漂移三态。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        _seed_minimal_repo(self.root)
        # 固定 branch，避免宿主 git 环境影响
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()
        self.addCleanup(self._branch_patcher.stop)

    # ------------------------------------------------------------------
    # AC-02 ①：首次生成
    # ------------------------------------------------------------------
    def test_update_generates_profile_first_run(self) -> None:
        """首次 update（profile 不存在）→ 落盘 + stderr 含"初始 hash"。"""
        profile_path = self.root / PROFILE_REL
        self.assertFalse(profile_path.exists())

        rc, _stdout, stderr = _run_update(self.root)
        self.assertEqual(rc, 0)
        self.assertTrue(
            profile_path.exists(),
            msg=f"profile not written; stderr={stderr}",
        )
        text = profile_path.read_text(encoding="utf-8")
        self.assertIn("schema: project-profile/v1", text)
        self.assertRegex(text, r"content_hash: [0-9a-f]{64}")
        # stderr 约定：首次生成打印"初始 hash: <short7>"
        self.assertRegex(
            stderr,
            r"project-profile 已生成（初始 hash: [0-9a-f]{7}）",
            msg=f"stderr missing first-run hash line; stderr={stderr}",
        )

    # ------------------------------------------------------------------
    # AC-02 ②：hash 稳定
    # ------------------------------------------------------------------
    def test_update_profile_hash_stable_on_second_run(self) -> None:
        """两次 update 项目描述未变 → content_hash 稳定 + stderr 不含"漂移"。"""
        _rc1, _s1, err1 = _run_update(self.root)
        self.assertIn("project-profile 已生成", err1)
        profile_path = self.root / PROFILE_REL
        text1 = profile_path.read_text(encoding="utf-8")
        hash1 = re.search(r"content_hash: ([0-9a-f]{64})", text1).group(1)

        _rc2, _s2, err2 = _run_update(self.root)
        text2 = profile_path.read_text(encoding="utf-8")
        hash2 = re.search(r"content_hash: ([0-9a-f]{64})", text2).group(1)
        self.assertEqual(
            hash1,
            hash2,
            msg="content_hash drifted without source change",
        )
        self.assertNotIn(
            "hash 漂移",
            err2,
            msg=f"unexpected drift announcement on stable run; stderr={err2}",
        )

    # ------------------------------------------------------------------
    # AC-02 ③：hash 漂移
    # ------------------------------------------------------------------
    def test_update_profile_drift_on_pyproject_change(self) -> None:
        """改 pyproject package_name → 第二次 update stderr 含"hash 漂移：<old>→<new>"。"""
        _rc1, _s1, err1 = _run_update(self.root)
        self.assertIn("project-profile 已生成", err1)
        profile_path = self.root / PROFILE_REL
        text1 = profile_path.read_text(encoding="utf-8")
        hash1_full = re.search(r"content_hash: ([0-9a-f]{64})", text1).group(1)
        hash1_short = hash1_full[:7]

        # 改描述：package_name sample-pkg → renamed-pkg
        (self.root / "pyproject.toml").write_text(
            """
[project]
name = "renamed-pkg"
dependencies = ["pyyaml>=6.0"]
""".lstrip(),
            encoding="utf-8",
        )

        _rc2, _s2, err2 = _run_update(self.root)
        text2 = profile_path.read_text(encoding="utf-8")
        hash2_full = re.search(r"content_hash: ([0-9a-f]{64})", text2).group(1)
        hash2_short = hash2_full[:7]
        self.assertNotEqual(hash1_full, hash2_full)
        self.assertIn("renamed-pkg", text2)
        # stderr 约定："project-profile 已刷新（hash 漂移：<old7>→<new7>）"
        expected_drift = f"hash 漂移：{hash1_short}→{hash2_short}"
        self.assertIn(
            expected_drift,
            err2,
            msg=f"drift line missing; want '{expected_drift}', stderr={err2}",
        )
        self.assertIn("project-profile 已刷新", err2)


class UpdateRepoUserAuthoredGuardTest(unittest.TestCase):
    """chg-02 回归守护：既有 _is_user_authored 路径在 profile 接入后仍生效。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        _seed_minimal_repo(self.root)
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()
        self.addCleanup(self._branch_patcher.stop)

    def test_update_skips_user_authored_claude_md(self) -> None:
        """用户自定义 CLAUDE.md（非模板 hash）→ update 不覆盖 + stderr 提示跳过。

        本用例不新增实现代码，仅守护 req-31 / chg-03 / sug-14 的既有路径：确保
        chg-02 的 profile 写盘扩展没有意外破坏用户自定义保护。
        """
        custom_text = "# my own CLAUDE.md\n\n项目专属指令 — 不应被 harness update 覆盖。\n"
        (self.root / "CLAUDE.md").write_text(custom_text, encoding="utf-8")

        rc, _stdout, stderr = _run_update(self.root)
        self.assertEqual(rc, 0)
        # CLAUDE.md 内容未被覆盖
        self.assertEqual(
            (self.root / "CLAUDE.md").read_text(encoding="utf-8"),
            custom_text,
        )
        # stderr 保留既有提示
        self.assertIn(
            "skipping user-authored file CLAUDE.md",
            stderr,
            msg=f"user-authored skip hint missing; stderr={stderr}",
        )


if __name__ == "__main__":
    unittest.main()
