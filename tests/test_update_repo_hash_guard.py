"""Tests for req-31（批量建议合集（20条））/ chg-03（CLI / helper 剩余修复）/ Step 1（sug-13）.

覆盖 sug-13（`update_repo` 多生成器共享文件 hash 竞争）的 `_write_with_hash_guard`
helper 行为：

- test_write_with_hash_guard_happy_path：正常写入 → sha256 匹配，返回 True。
- test_write_with_hash_guard_reverts_on_mismatch：mock `Path.read_text` 第二次返回
  不同内容 → 触发 rollback + stderr WARNING + 返回 False。
"""

from __future__ import annotations

import hashlib
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


class WriteWithHashGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_write_with_hash_guard_happy_path(self) -> None:
        """正常写入：文件不存在 → 写入成功，sha256 匹配，返回 True。"""
        from harness_workflow.workflow_helpers import _write_with_hash_guard

        target = self.root / "shared.md"
        content = "# shared content v1\n"
        ok = _write_with_hash_guard(target, content)
        self.assertTrue(ok)
        self.assertEqual(target.read_text(encoding="utf-8"), content)
        self.assertEqual(
            hashlib.sha256(target.read_text(encoding="utf-8").encode()).hexdigest(),
            hashlib.sha256(content.encode()).hexdigest(),
        )

    def test_write_with_hash_guard_reverts_on_mismatch(self) -> None:
        """模拟并发覆盖：二次读回内容 hash 与期望不匹配 → 回滚 + WARNING + 返回 False。"""
        from harness_workflow import workflow_helpers
        from harness_workflow.workflow_helpers import _write_with_hash_guard

        target = self.root / "runtime.yaml"
        old = "old: v0\n"
        target.write_text(old, encoding="utf-8")
        new = "new: v1\n"

        # 让第二次 read_text（verify 阶段）返回被第三方并发覆盖过的内容
        original_read_text = Path.read_text
        call_counter = {"count": 0}

        def _fake_read_text(self: Path, *args, **kwargs) -> str:
            if self == target:
                call_counter["count"] += 1
                # 第一次（读 old）返回真实内容；第二次（verify）返回被并发篡改的内容
                if call_counter["count"] == 2:
                    return "concurrently overwritten\n"
            return original_read_text(self, *args, **kwargs)

        stderr_buf = io.StringIO()
        with mock.patch.object(Path, "read_text", _fake_read_text), redirect_stderr(stderr_buf):
            ok = _write_with_hash_guard(target, new)

        self.assertFalse(ok)
        # 回滚：文件内容回到 old
        self.assertEqual(target.read_text(encoding="utf-8"), old)
        self.assertIn("hash mismatch", stderr_buf.getvalue())


if __name__ == "__main__":
    unittest.main()
