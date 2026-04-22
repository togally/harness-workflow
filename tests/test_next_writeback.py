"""Unit tests for `workflow_next` / `_sync_stage_to_state_yaml`（req-26 / chg-03）。

覆盖 AC-03：
- `harness next` 推进 stage 后，`.workflow/state/requirements/{id}.yaml` 的 `stage`
  字段随 runtime.yaml 同步写回；
- 推进至 `done` 时，state yaml 的 `status` 从 `active` 变为 `done`；
- `operation_type=bugfix` 时写的是 `.workflow/state/bugfixes/{id}.yaml`；
- 即使 runtime.yaml 缺 `operation_target`，只要有 `current_requirement` 也必须写回
  （对应 bug 活证：runtime.yaml 只有 current_requirement，state yaml 停在
  requirement_review 从不更新）。

Helper 层直接调用 `workflow_next`，不跑真 CLI（briefing 硬约束）。
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


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


def _write_runtime(
    root: Path,
    *,
    stage: str,
    operation_type: str = "requirement",
    operation_target: str = "",
    current_requirement: str = "",
    active_ids: list[str] | None = None,
) -> None:
    active_ids = active_ids or []
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
    ]
    if active_ids:
        lines.append("active_requirements:")
        for aid in active_ids:
            lines.append(f"  - {aid}")
    else:
        lines.append("active_requirements: []")
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
                'created_at: "2026-04-19"',
                'started_at: "2026-04-19"',
                'completed_at: ""',
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


def _seed_bugfix_state(
    root: Path,
    bugfix_id: str,
    slug: str,
    title: str,
    *,
    stage: str = "regression",
    status: str = "active",
) -> Path:
    state_path = (
        root / ".workflow" / "state" / "bugfixes" / f"{bugfix_id}-{slug}.yaml"
    )
    _write(
        state_path,
        "\n".join(
            [
                f'id: "{bugfix_id}"',
                f'title: "{title}"',
                f'stage: "{stage}"',
                f'status: "{status}"',
                "",
            ]
        ),
    )
    return state_path


class NextWritebackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-next-writeback-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_next_writes_stage_to_requirement_yaml(self) -> None:
        """推进 requirement_review → planning，req yaml 必须同步。

        P-1 default-pick C（req-31 chg-01）：改测试断言对齐新 stage 序列；planning 替代 changes_review。
        模拟的是 bug 活证场景：runtime.yaml 有 current_requirement 但缺
        operation_target，旧实现会跳过写回；修复后必须基于 current_requirement 兜底。
        """
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        state_path = _seed_requirement_state(
            self.root, "req-26", "uav-split", "UAV Split",
            stage="requirement_review", status="active",
        )
        _write_runtime(
            self.root,
            stage="requirement_review",
            operation_type="requirement",
            operation_target="",  # 关键：缺 operation_target，走 current_requirement 回退
            current_requirement="req-26",
            active_ids=["req-26"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "planning",
                         msg=f"state yaml stage should be planning, got {state!r}")
        # status 尚未 done，应保持 active
        self.assertEqual(state.get("status"), "active")

    def test_next_writes_done_status(self) -> None:
        """推到 done 时 status 从 active 变为 done，completed_at 非空。"""
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        state_path = _seed_requirement_state(
            self.root, "req-99", "demo", "Demo",
            stage="acceptance", status="active",
        )
        _write_runtime(
            self.root,
            stage="acceptance",
            operation_type="requirement",
            operation_target="req-99",
            current_requirement="req-99",
            active_ids=["req-99"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        state = load_simple_yaml(state_path)
        self.assertEqual(state.get("stage"), "done")
        self.assertEqual(state.get("status"), "done")
        # completed_at 应被写入（非空）
        completed_at = str(state.get("completed_at", "")).strip()
        self.assertTrue(
            completed_at and completed_at not in ('""', "''"),
            f"completed_at should be set, got {completed_at!r}",
        )

    def test_next_writes_bugfix_yaml(self) -> None:
        """operation_type=bugfix 时，写 `.workflow/state/bugfixes/{id}.yaml`。"""
        from harness_workflow.workflow_helpers import (
            load_simple_yaml,
            workflow_next,
        )

        bugfix_state_path = _seed_bugfix_state(
            self.root, "bugfix-7", "login-crash", "Login Crash",
            stage="regression", status="active",
        )
        _write_runtime(
            self.root,
            stage="regression",
            operation_type="bugfix",
            operation_target="bugfix-7",
            current_requirement="bugfix-7",
            active_ids=["bugfix-7"],
        )

        rc = workflow_next(self.root, execute=False)
        self.assertEqual(rc, 0)

        state = load_simple_yaml(bugfix_state_path)
        # BUGFIX_SEQUENCE: regression → executing
        self.assertEqual(state.get("stage"), "executing")
        self.assertEqual(state.get("status"), "active")

        # 确认 requirement state yaml 没被误改
        req_dir = self.root / ".workflow" / "state" / "requirements"
        self.assertEqual([p for p in req_dir.iterdir() if p.is_file()], [])


if __name__ == "__main__":
    unittest.main()
