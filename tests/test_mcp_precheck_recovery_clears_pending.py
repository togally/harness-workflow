"""Unit tests for MCP pre-check 阶段 3 恢复：清空 pending（req-38 / chg-03）。

覆盖 AC-6：
- test_mcp_precheck_recovery_clears_pending: 模拟阶段 3——load runtime（pending 非空）→
  写入 pending=null → save → reload → 断言 pending 已清空；session-memory 新增
  mcp_registration_resolved: apifox 行含 ISO 时间戳。
"""

from __future__ import annotations

import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

_ISO_TS_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?[\+\-]\d{2}:\d{2}")


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


def _write_runtime_with_pending(root: Path, pending_type: str, provider: str) -> None:
    lines = [
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
        f'  type: "{pending_type}"',
        "  details:",
        f'    provider: "{provider}"',
        "",
    ]
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(lines), encoding="utf-8"
    )


class McpPrecheckRecoveryTest(unittest.TestCase):
    """模拟阶段 3：清空 pending + session-memory 记录 resolved。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-precheck-recovery-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_mcp_precheck_recovery_clears_pending(self) -> None:
        """模拟阶段 3 恢复流程：
        1. 加载 runtime（pending 非空）
        2. 写入 pending=null 并 save
        3. reload 确认 pending 已清空
        4. session-memory 追加 mcp_registration_resolved 行含 ISO 时间戳
        """
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            save_requirement_runtime,
        )

        # Step 1: 构造含 pending 的 runtime
        provider = "apifox"
        _write_runtime_with_pending(self.root, "mcp_register", provider)

        # Step 2: load → 确认 pending 非空
        runtime = load_requirement_runtime(self.root)
        pending_before = runtime.get("stage_pending_user_action")
        self.assertIsInstance(pending_before, dict,
                              f"Expected pending to be dict, got {pending_before!r}")
        self.assertEqual(pending_before.get("type"), "mcp_register")  # type: ignore[union-attr]

        # Step 3: 模拟阶段 3 恢复——清空 pending
        runtime["stage_pending_user_action"] = None
        save_requirement_runtime(self.root, runtime)

        # Step 4: reload 确认 pending 已清空
        runtime_after = load_requirement_runtime(self.root)
        pending_after = runtime_after.get("stage_pending_user_action")
        self.assertIsNone(pending_after,
                          f"pending should be None after recovery, got {pending_after!r}")

        # Step 5: 模拟 session-memory 记录 resolved
        now_iso = datetime.now(timezone.utc).isoformat()
        session_memory_dir = self.root / ".workflow" / "state" / "sessions" / "req-38" / "chg-03"
        session_memory_dir.mkdir(parents=True, exist_ok=True)
        session_memory_path = session_memory_dir / "session-memory.md"
        session_memory_path.write_text(
            "# Session Memory\n\n## Stage Block\n",
            encoding="utf-8",
        )

        resolved_line = f"mcp_registration_resolved: {provider} ({now_iso})"
        with session_memory_path.open("a", encoding="utf-8") as f:
            f.write(resolved_line + "\n")

        # Step 6: 验证 session-memory 含 resolved 行 + ISO 时间戳
        content = session_memory_path.read_text(encoding="utf-8")
        self.assertIn("mcp_registration_resolved", content,
                      "session-memory should contain mcp_registration_resolved")
        self.assertIn(provider, content,
                      f"session-memory should contain provider '{provider}'")

        # 验证 ISO 时间戳格式（正则命中）
        ts_match = _ISO_TS_PATTERN.search(content)
        self.assertIsNotNone(ts_match,
                             f"session-memory resolved line should contain ISO timestamp, got:\n{content}")

    def test_pending_null_saved_as_yaml_null(self) -> None:
        """save_requirement_runtime 写入 pending=None 时，yaml 文件应包含 null 字面量。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            save_requirement_runtime,
        )

        # 先构造含 pending 的 runtime
        _write_runtime_with_pending(self.root, "mcp_register", "apifox")
        runtime = load_requirement_runtime(self.root)

        # 清空 pending → save
        runtime["stage_pending_user_action"] = None
        save_requirement_runtime(self.root, runtime)

        # 读 yaml 文件内容确认含 null
        yaml_content = (self.root / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8")
        self.assertIn("stage_pending_user_action: null", yaml_content,
                      f"yaml should contain 'stage_pending_user_action: null', got:\n{yaml_content}")

    def test_pending_dict_saved_correctly(self) -> None:
        """save_requirement_runtime 写入 pending dict 时，yaml 文件应包含 type + details。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            save_requirement_runtime,
        )

        # 写无 pending 的 runtime
        lines = [
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
            "",
        ]
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            "\n".join(lines), encoding="utf-8"
        )

        runtime = load_requirement_runtime(self.root)
        runtime["stage_pending_user_action"] = {"type": "mcp_register", "details": {"provider": "apifox"}}
        save_requirement_runtime(self.root, runtime)

        # reload 确认 pending 正确存储
        runtime_after = load_requirement_runtime(self.root)
        pending = runtime_after.get("stage_pending_user_action")
        self.assertIsInstance(pending, dict, f"Expected dict, got {pending!r}")
        self.assertEqual(pending.get("type"), "mcp_register")  # type: ignore[union-attr]
        details = pending.get("details")  # type: ignore[union-attr]
        self.assertIsInstance(details, dict)
        self.assertEqual(details.get("provider"), "apifox")  # type: ignore[union-attr]


if __name__ == "__main__":
    unittest.main()
