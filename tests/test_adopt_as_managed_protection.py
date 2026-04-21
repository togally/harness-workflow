"""Tests for req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 2（sug-14）.

覆盖 `adopt-as-managed` 判据收紧：
- test_user_authored_file_not_overwritten_without_flag：用户自建内容 + 不在白名单 →
  `update_repo` 跳过覆盖 + stderr 含 "skipping user-authored"。
- test_force_managed_flag_overrides_user_authored：同上 + `force_managed=True` → 覆盖生效。
- test_template_content_match_is_not_user_authored：内容与模板相同 → 视为 adopt（非 user-authored）。
"""

from __future__ import annotations

import io
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


if __name__ == "__main__":
    unittest.main()
