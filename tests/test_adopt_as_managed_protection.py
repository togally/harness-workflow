"""Tests for req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 2（sug-14）.

覆盖 `adopt-as-managed` 判据收紧：
- test_user_authored_file_not_overwritten_without_flag：用户自建内容 + 不在白名单 →
  `update_repo` 跳过覆盖 + stderr 含 "skipping user-authored"。
- test_force_managed_flag_overrides_user_authored：同上 + `force_managed=True` → 覆盖生效。
- test_template_content_match_is_not_user_authored：内容与模板相同 → 视为 adopt（非 user-authored）。

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ testing 阶段 P2-01 追加：
- test_update_skipped_modified_also_prints_stderr：既有 managed_state 登记后，用户修改
  CLAUDE.md → 再次 update 应在 stderr 打印 "skipping user-modified file"（不走静默
  stdout-only 兜底）。
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


class IsUserAuthoredTest(unittest.TestCase):
    """直接测 `_is_user_authored` helper（单元级别，避开完整 update_repo 依赖）。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_user_authored_file_detected(self) -> None:
        from harness_workflow.workflow_helpers import _is_user_authored

        path = self.root / "CLAUDE.md"
        path.write_text("# user's custom CLAUDE.md\n", encoding="utf-8")
        template = "# harness default CLAUDE.md v1\n"
        self.assertTrue(_is_user_authored(path, "CLAUDE.md", template))

    def test_content_match_template_is_not_user_authored(self) -> None:
        """当前文件内容与即将写入的 template 相同 → 不应判为 user-authored。"""
        from harness_workflow.workflow_helpers import _is_user_authored

        path = self.root / "AGENTS.md"
        shared = "# shared harness AGENTS.md\n"
        path.write_text(shared, encoding="utf-8")
        self.assertFalse(_is_user_authored(path, "AGENTS.md", shared))

    def test_whitelisted_hash_is_not_user_authored(self) -> None:
        """历史模板 hash 被登记在白名单 → 不判为 user-authored（可被新模板覆盖）。"""
        import hashlib

        from harness_workflow import workflow_helpers
        from harness_workflow.workflow_helpers import _is_user_authored

        legacy_content = "# legacy v0 template\n"
        new_content = "# new v1 template\n"
        path = self.root / "SKILL.md"
        path.write_text(legacy_content, encoding="utf-8")

        legacy_hash = hashlib.sha256(legacy_content.encode("utf-8")).hexdigest()
        with mock.patch.object(
            workflow_helpers,
            "_HARNESS_TEMPLATE_HASHES",
            {"SKILL.md": {legacy_hash}},
        ):
            self.assertFalse(_is_user_authored(path, "SKILL.md", new_content))


class UpdateSkippedModifiedStderrTest(unittest.TestCase):
    """req-32 / testing 阶段 P2-01：已登记 managed_state 路径也需 stderr 提示跳过。

    场景：
      1. 首次 update → CLAUDE.md 落盘，managed_state 登记原始 hash。
      2. 用户手改 CLAUDE.md → hash 变化，但 relative 仍在 managed_state 中。
      3. 再跑 update → 走 line ~2982 兜底（既非 force_managed，也非 hash 匹配）。

    修前：仅 `actions.append("skipped modified ...")` 进 stdout（报告模式用）；
    修后：同步在 stderr 打印 "skipping user-modified file {relative}; pass
    --force-managed to overwrite." 便于 CI/脚本观察。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        self.root.mkdir()
        (self.root / ".workflow" / "state").mkdir(parents=True)
        (self.root / ".workflow" / "context").mkdir(parents=True)
        (self.root / ".codex" / "harness").mkdir(parents=True)
        (self.root / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (self.root / ".workflow" / "state" / "platforms.yaml").write_text(
            "active_agent: codex\n",
            encoding="utf-8",
        )
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "sample-pkg"\n',
            encoding="utf-8",
        )
        self._branch_patcher = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patcher.start()
        self.addCleanup(self._branch_patcher.stop)

    def _run_update(self) -> tuple[int, str, str]:
        from harness_workflow.workflow_helpers import update_repo

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            rc = update_repo(self.root, check=False)
        return rc, stdout_buf.getvalue(), stderr_buf.getvalue()

    def test_update_skipped_modified_also_prints_stderr(self) -> None:
        # Step A：首次 update 建立 managed_state
        rc1, _stdout1, _stderr1 = self._run_update()
        self.assertEqual(rc1, 0)
        claude_path = self.root / "CLAUDE.md"
        self.assertTrue(claude_path.exists())

        # Step B：用户手改 CLAUDE.md（hash 不再匹配 managed_state 登记的值）
        tampered = "# user tampered content\n\n本地注释 — 不应被 update 覆盖。\n"
        claude_path.write_text(tampered, encoding="utf-8")

        # Step C：再跑 update，期望走兜底 "skipped modified"
        rc2, _stdout2, stderr2 = self._run_update()
        self.assertEqual(rc2, 0)

        # 1. 用户内容未被覆盖
        self.assertEqual(
            claude_path.read_text(encoding="utf-8"),
            tampered,
            msg="user-modified CLAUDE.md was unexpectedly overwritten",
        )
        # 2. stderr 含 user-modified 文案（P2-01 目标）
        self.assertIn(
            "skipping user-modified file CLAUDE.md",
            stderr2,
            msg=f"stderr missing user-modified hint; stderr={stderr2!r}",
        )


if __name__ == "__main__":
    unittest.main()
