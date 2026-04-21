"""Tests for create_suggestion frontmatter 五字段 + 校验（req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 1.2）。

覆盖 chg-01 change.md §5.1 + plan.md Step 1 对 create_suggestion 的三条断言：

- test_case_a：title=None → SystemExit（契约 6 要求 title 必填）。
- test_case_b：priority 非 `high/medium/low` 之一 → SystemExit（priority 白名单）。
- test_case_c：正常调用，frontmatter 必含五字段 `id` / `title` / `status: pending`
  / `created_at` / `priority`（契约 6 五字段）。

Helper 层直接调用 workflow_helpers 函数；tempdir 隔离。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


class CreateSuggestionFrontmatterTest(unittest.TestCase):
    """chg-01 Step 1.2：create_suggestion 五字段 + 必填 / 白名单校验。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-cs-fm-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    # ---------- test_case_a: title 必填 ----------
    def test_create_suggestion_requires_title(self) -> None:
        """title=None → SystemExit（契约 6 要求 title 必填）。"""
        from harness_workflow.workflow_helpers import create_suggestion

        with self.assertRaises(SystemExit):
            create_suggestion(self.root, "一条没有 title 的建议正文", title=None)

    # ---------- test_case_b: priority 白名单 ----------
    def test_create_suggestion_rejects_invalid_priority(self) -> None:
        """priority 非 `high/medium/low` 之一 → SystemExit。"""
        from harness_workflow.workflow_helpers import create_suggestion

        with self.assertRaises(SystemExit):
            create_suggestion(
                self.root,
                "正文内容",
                title="合法标题",
                priority="urgent",
            )

    # ---------- test_case_c: 五字段齐全 ----------
    def test_create_suggestion_writes_five_fields(self) -> None:
        """正常调用产出 frontmatter 必含 id / title / status / created_at / priority 五字段。"""
        from harness_workflow.workflow_helpers import create_suggestion

        rc = create_suggestion(
            self.root,
            "示例建议正文",
            title="新增 suggest frontmatter 校验",
            priority="high",
        )
        self.assertEqual(rc, 0)

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        files = sorted(sug_dir.glob("sug-*.md"))
        self.assertEqual(len(files), 1, f"应新增 1 个 sug 文件，实际 {files}")
        text = files[0].read_text(encoding="utf-8")

        # 五字段逐条硬断言
        self.assertIn("id: sug-", text, "frontmatter 应含 id 字段")
        self.assertIn("title:", text, "frontmatter 应含 title 字段")
        self.assertIn("新增 suggest frontmatter 校验", text, "title 值应落盘")
        self.assertIn("status: pending", text, "frontmatter 初始 status 应为 pending")
        self.assertIn("created_at:", text, "frontmatter 应含 created_at 字段")
        self.assertIn("priority: high", text, "priority 应落盘为 high")


if __name__ == "__main__":
    unittest.main()
