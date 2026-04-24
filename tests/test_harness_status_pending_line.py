"""Unit tests for `workflow_status` pending 行输出（req-38 / chg-03）。

覆盖 AC-5 + AC-6：
- test_harness_status_pending_line_when_set: pending 非空时 status 输出含 Pending User Action 行。
- test_harness_status_pending_line_when_none: pending 为 None / 缺失时 status 输出含 None 标记。
"""

from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime(root: Path, lines: list[str]) -> None:
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


class StatusPendingLineTest(unittest.TestCase):
    """harness status 输出 Pending User Action 行。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-status-pending-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_harness_status_pending_line_when_set(self) -> None:
        """pending 非空时 status 输出含 Pending User Action: mcp_register(provider=apifox)。"""
        from harness_workflow.workflow_helpers import workflow_status

        _write_runtime(self.root, [
            'operation_type: "requirement"',
            'operation_target: "req-38"',
            'current_requirement: "req-38"',
            'stage: "executing"',
            'conversation_mode: "open"',
            'locked_requirement: ""',
            'locked_stage: ""',
            'current_regression: ""',
            "ff_mode: false",
            "ff_stage_history: []",
            "active_requirements:",
            "  - req-38",
            "stage_pending_user_action:",
            '  type: "mcp_register"',
            "  details:",
            '    provider: "apifox"',
        ])

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            rc = workflow_status(self.root)

        self.assertEqual(rc, 0)
        output = stdout_buf.getvalue()
        self.assertIn("Pending User Action:", output,
                      f"Expected 'Pending User Action:' in output, got:\n{output}")
        self.assertIn("mcp_register", output,
                      f"Expected 'mcp_register' in pending line, got:\n{output}")
        self.assertIn("apifox", output,
                      f"Expected 'apifox' in pending line, got:\n{output}")
        # 不应包含 None
        # 找到 pending 行
        pending_line = next(
            (ln for ln in output.splitlines() if "Pending User Action:" in ln), ""
        )
        self.assertNotIn("None", pending_line,
                         f"Pending line should not say None when set: {pending_line!r}")

    def test_harness_status_pending_line_when_none(self) -> None:
        """pending 为 null 时 status 输出含 Pending User Action: None。"""
        from harness_workflow.workflow_helpers import workflow_status

        _write_runtime(self.root, [
            'operation_type: "requirement"',
            'operation_target: "req-38"',
            'current_requirement: "req-38"',
            'stage: "executing"',
            'conversation_mode: "open"',
            'locked_requirement: ""',
            'locked_stage: ""',
            'current_regression: ""',
            "ff_mode: false",
            "ff_stage_history: []",
            "active_requirements:",
            "  - req-38",
            "stage_pending_user_action: null",
        ])

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            rc = workflow_status(self.root)

        self.assertEqual(rc, 0)
        output = stdout_buf.getvalue()
        self.assertIn("Pending User Action: None", output,
                      f"Expected 'Pending User Action: None', got:\n{output}")

    def test_harness_status_pending_line_when_field_missing(self) -> None:
        """旧 runtime（无 stage_pending_user_action 字段）→ status 输出含 Pending User Action: None。"""
        from harness_workflow.workflow_helpers import workflow_status

        # 旧格式 runtime，无 pending 字段
        _write_runtime(self.root, [
            'operation_type: "requirement"',
            'operation_target: "req-38"',
            'current_requirement: "req-38"',
            'stage: "executing"',
            'conversation_mode: "open"',
            'locked_requirement: ""',
            'locked_stage: ""',
            'current_regression: ""',
            "ff_mode: false",
            "ff_stage_history: []",
            "active_requirements:",
            "  - req-38",
        ])

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            rc = workflow_status(self.root)

        self.assertEqual(rc, 0)
        output = stdout_buf.getvalue()
        self.assertIn("Pending User Action: None", output,
                      f"Expected 'Pending User Action: None', got:\n{output}")


if __name__ == "__main__":
    unittest.main()
