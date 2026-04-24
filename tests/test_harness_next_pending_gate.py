"""Unit tests for `workflow_next` pending gate（req-38 / chg-03）。

覆盖 AC-5 + AC-6：
- test_harness_next_pending_gate_blocks: stage_pending_user_action 非空时拒推进，
  退出码非 0，stderr 含阻塞原因，runtime stage / stage_history 不变。
- test_harness_next_pending_gate_allows: stage_pending_user_action 为 null / 缺失时正常推进，
  退出码 0，stage_history 追加。
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime_with_pending(
    root: Path,
    *,
    stage: str,
    pending: object = None,
    operation_type: str = "requirement",
    operation_target: str = "req-38",
    current_requirement: str = "req-38",
) -> None:
    """写 runtime.yaml，可选附带 stage_pending_user_action 字段。"""
    lines = [
        f'operation_type: "{operation_type}"',
        f'operation_target: "{operation_target}"',
        f'current_requirement: "{current_requirement}"',
        f'stage: "{stage}"',
        'conversation_mode: "open"',
        'locked_requirement: ""',
        'locked_stage: ""',
        'current_regression: ""',
        "ff_mode: false",
        "ff_stage_history: []",
        "active_requirements:",
        f"  - {current_requirement}",
    ]
    if pending is None:
        lines.append("stage_pending_user_action: null")
    elif isinstance(pending, dict):
        lines.append("stage_pending_user_action:")
        for k, v in pending.items():
            if isinstance(v, dict):
                lines.append(f"  {k}:")
                for kk, vv in v.items():
                    lines.append(f'    {kk}: "{vv}"')
            else:
                lines.append(f'  {k}: "{v}"')
    lines.append("")
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def _seed_requirement_state(
    root: Path,
    req_id: str,
    slug: str,
    title: str,
    *,
    stage: str = "requirement_review",
    status: str = "active",
) -> Path:
    state_path = (
        root / ".workflow" / "state" / "requirements" / f"{req_id}-{slug}.yaml"
    )
    _write(
        state_path,
        "\n".join(
            [
                f'id: "{req_id}"',
                f'title: "{title}"',
                f'stage: "{stage}"',
                f'status: "{status}"',
                'created_at: "2026-04-23"',
                'started_at: "2026-04-23"',
                'completed_at: ""',
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


class PendingGateBlocksTest(unittest.TestCase):
    """AC-5: pending 非空时 harness next 拒推进。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-pending-blocks-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_harness_next_pending_gate_blocks(self) -> None:
        """stage_pending_user_action 非空 → 退出码非 0 + stderr 含阻塞原因 + stage/history 不变。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            workflow_next,
        )

        _seed_requirement_state(
            self.root, "req-38", "test-pending", "Test Pending",
            stage="executing", status="active",
        )
        _write_runtime_with_pending(
            self.root,
            stage="executing",
            pending={"type": "mcp_register", "details": {"provider": "apifox"}},
        )

        # 捕获 stderr
        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            rc = workflow_next(self.root, execute=False)

        stderr_output = stderr_buf.getvalue()

        # 退出码非 0
        self.assertNotEqual(rc, 0, f"Expected non-zero exit code, got {rc}")

        # stderr 含阻塞原因
        self.assertIn("stage 正在等待 mcp_register", stderr_output,
                      f"stderr should contain blocking reason, got: {stderr_output!r}")

        # stage 未变
        runtime_after = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime_after.get("stage", "")).strip(), "executing",
                         "stage must not advance when pending gate blocks")

    def test_harness_next_pending_gate_exit_code_is_3(self) -> None:
        """退出码应为 3（pending 专用非零退出码）。"""
        from harness_workflow.workflow_helpers import workflow_next

        _seed_requirement_state(
            self.root, "req-38", "test-pending-rc", "Test Pending RC",
            stage="executing", status="active",
        )
        _write_runtime_with_pending(
            self.root,
            stage="executing",
            pending={"type": "mcp_register", "details": {"provider": "apifox"}},
        )

        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            rc = workflow_next(self.root, execute=False)

        self.assertEqual(rc, 3, f"Expected exit code 3 (pending gate), got {rc}")

    def test_harness_next_pending_stderr_contains_details(self) -> None:
        """stderr 应包含 details 中的 provider 名称。"""
        from harness_workflow.workflow_helpers import workflow_next

        _seed_requirement_state(
            self.root, "req-38", "test-pending-detail", "Test Pending Detail",
            stage="executing", status="active",
        )
        _write_runtime_with_pending(
            self.root,
            stage="executing",
            pending={"type": "mcp_register", "details": {"provider": "apifox"}},
        )

        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            workflow_next(self.root, execute=False)

        stderr_output = stderr_buf.getvalue()
        self.assertIn("apifox", stderr_output,
                      f"stderr should contain provider detail, got: {stderr_output!r}")


class PendingGateAllowsTest(unittest.TestCase):
    """AC-6: pending 为 null / 缺失时 harness next 正常推进。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-pending-allows-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_harness_next_pending_gate_allows_when_null(self) -> None:
        """stage_pending_user_action: null → 正常推进，退出码 0。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            workflow_next,
        )

        _seed_requirement_state(
            self.root, "req-38", "test-null-pending", "Test Null Pending",
            stage="requirement_review", status="active",
        )
        _write_runtime_with_pending(
            self.root,
            stage="requirement_review",
            pending=None,  # null
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0, f"Expected exit code 0 (no pending), got {rc}")

        runtime_after = load_requirement_runtime(self.root)
        new_stage = str(runtime_after.get("stage", "")).strip()
        self.assertEqual(new_stage, "planning",
                         f"stage should advance to planning, got {new_stage!r}")

    def test_harness_next_pending_gate_allows_when_missing(self) -> None:
        """stage_pending_user_action 字段缺失（旧 runtime）→ 正常推进，退出码 0。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            workflow_next,
        )

        _seed_requirement_state(
            self.root, "req-38", "test-missing-pending", "Test Missing Pending",
            stage="requirement_review", status="active",
        )
        # 写旧格式 runtime（不含 stage_pending_user_action 字段）
        lines = [
            'operation_type: "requirement"',
            'operation_target: "req-38"',
            'current_requirement: "req-38"',
            'stage: "requirement_review"',
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

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0, f"Expected exit code 0 (missing pending field), got {rc}")

        runtime_after = load_requirement_runtime(self.root)
        new_stage = str(runtime_after.get("stage", "")).strip()
        self.assertEqual(new_stage, "planning",
                         f"stage should advance to planning, got {new_stage!r}")


if __name__ == "__main__":
    unittest.main()
