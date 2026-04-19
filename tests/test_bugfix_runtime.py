"""Unit tests for bugfix runtime persistence（req-28 / chg-02，覆盖 AC-12）。

覆盖场景：
- `create_bugfix` 后 runtime.yaml 必须包含 `operation_type="bugfix"` 与 `operation_target`；
- `save_requirement_runtime` → `load_requirement_runtime` 往返多次后字段仍在（旧实现因
  ordered_keys 白名单裁剪，首轮 save 就丢字段）；
- `workflow_next` 推进 bugfix stage 后，`.workflow/state/bugfixes/{id}.yaml` 的 stage
  字段与 runtime.yaml 一致（AC-03 对 bugfix 生效）；
- 懒回填策略：runtime.yaml 手工丢掉 `operation_type` 后，下一次 `load` 能从
  `current_requirement` 前缀（`bugfix-` / `sug-` / 其他）推断回来。

Helper 层直接调用，不跑真 CLI（briefing 硬约束）。
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
    # 最小的 runtime.yaml，避免 create_bugfix 读不到文件
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                'operation_type: ""',
                'operation_target: ""',
                'current_requirement: ""',
                'stage: ""',
                'conversation_mode: "open"',
                'locked_requirement: ""',
                'locked_stage: ""',
                'current_regression: ""',
                "ff_mode: false",
                "ff_stage_history: []",
                "active_requirements: []",
                "",
            ]
        ),
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


class BugfixRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-bugfix-runtime-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir)

    def test_create_bugfix_writes_operation_type(self) -> None:
        """`create_bugfix` 完成后，runtime.yaml 必须同时写入
        `operation_type="bugfix"` 与 `operation_target="bugfix-N"`。"""
        from harness_workflow.workflow_helpers import (
            create_bugfix,
            load_requirement_runtime,
        )

        rc = create_bugfix(self.root, name="smoke")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        self.assertEqual(runtime.get("operation_type"), "bugfix")
        target = str(runtime.get("operation_target", "")).strip()
        self.assertTrue(
            target.startswith("bugfix-"),
            msg=f"operation_target should start with 'bugfix-', got {target!r}",
        )
        # current_requirement 亦应同步到该 bugfix id（兼容字段）
        self.assertEqual(runtime.get("current_requirement"), target)
        # stage 初始应为 regression
        self.assertEqual(runtime.get("stage"), "regression")

    def test_operation_type_survives_save_reload(self) -> None:
        """save → load → save → load 往返多次后，`operation_type` 与
        `operation_target` 字段仍在（旧实现因 ordered_keys 白名单首轮即丢）。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            save_requirement_runtime,
        )

        _write_runtime(
            self.root,
            stage="regression",
            operation_type="bugfix",
            operation_target="bugfix-42",
            current_requirement="bugfix-42",
            active_ids=["bugfix-42"],
        )

        for _ in range(2):
            runtime = load_requirement_runtime(self.root)
            self.assertEqual(
                runtime.get("operation_type"),
                "bugfix",
                msg=f"operation_type lost after save/load round-trip: {runtime!r}",
            )
            self.assertEqual(runtime.get("operation_target"), "bugfix-42")
            save_requirement_runtime(self.root, runtime)

        final = load_requirement_runtime(self.root)
        self.assertEqual(final.get("operation_type"), "bugfix")
        self.assertEqual(final.get("operation_target"), "bugfix-42")
        self.assertEqual(final.get("current_requirement"), "bugfix-42")
        self.assertEqual(final.get("stage"), "regression")

        # 同时确认文件里确实有这两行（不是仅靠懒回填撑起来的）
        text = (self.root / ".workflow" / "state" / "runtime.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("operation_type:", text)
        self.assertIn("operation_target:", text)
        self.assertIn("bugfix", text)

    def test_next_advances_bugfix_stage_in_yaml(self) -> None:
        """`create_bugfix` 后执行 `workflow_next`，推进 bugfix stage，
        `.workflow/state/bugfixes/{id}.yaml` 的 stage 必须与 runtime 一致。"""
        from harness_workflow.workflow_helpers import (
            create_bugfix,
            load_requirement_runtime,
            load_simple_yaml,
            workflow_next,
        )

        rc = create_bugfix(self.root, name="loop-closure")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        bugfix_id = str(runtime.get("operation_target", "")).strip()
        self.assertTrue(bugfix_id.startswith("bugfix-"))

        # 推进 regression → executing
        rc2 = workflow_next(self.root, execute=False)
        self.assertEqual(rc2, 0)

        runtime_after = load_requirement_runtime(self.root)
        self.assertEqual(runtime_after.get("stage"), "executing")
        # operation_type / operation_target 在推进后必须保留
        self.assertEqual(runtime_after.get("operation_type"), "bugfix")
        self.assertEqual(runtime_after.get("operation_target"), bugfix_id)

        # bugfix yaml 的 stage 亦应同步到 executing
        bugfix_state_dir = self.root / ".workflow" / "state" / "bugfixes"
        candidates = [
            p for p in bugfix_state_dir.iterdir()
            if p.is_file()
            and p.suffix == ".yaml"
            and (p.stem == bugfix_id or p.stem.startswith(bugfix_id + "-"))
        ]
        self.assertEqual(
            len(candidates),
            1,
            msg=f"expected exactly one bugfix state yaml, got {candidates!r}",
        )
        state = load_simple_yaml(candidates[0])
        self.assertEqual(
            state.get("stage"),
            "executing",
            msg=f"bugfix state yaml stage should sync to runtime, got {state!r}",
        )

    def test_lazy_backfill_operation_type_from_current_requirement(self) -> None:
        """若 runtime.yaml 中手工清空 `operation_type`，下一次 `load_requirement_runtime`
        应从 `current_requirement` 前缀推断（bugfix-* → bugfix；sug-* → suggestion；
        其余 → requirement）。"""
        from harness_workflow.workflow_helpers import load_requirement_runtime

        # 场景 1：current_requirement=bugfix-6，但 operation_type 为空
        _write_runtime(
            self.root,
            stage="regression",
            operation_type="",
            operation_target="",
            current_requirement="bugfix-6",
            active_ids=["bugfix-6"],
        )
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(
            runtime.get("operation_type"),
            "bugfix",
            msg="lazy-backfill should infer bugfix from current_requirement prefix",
        )
        self.assertEqual(runtime.get("operation_target"), "bugfix-6")

        # 场景 2：current_requirement=sug-12 → suggestion
        _write_runtime(
            self.root,
            stage="suggestion",
            operation_type="",
            operation_target="",
            current_requirement="sug-12",
        )
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(runtime.get("operation_type"), "suggestion")
        self.assertEqual(runtime.get("operation_target"), "sug-12")

        # 场景 3：current_requirement=req-28 → requirement
        _write_runtime(
            self.root,
            stage="executing",
            operation_type="",
            operation_target="",
            current_requirement="req-28",
        )
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(runtime.get("operation_type"), "requirement")
        self.assertEqual(runtime.get("operation_target"), "req-28")

        # 场景 4：显式非空值必须保留，不被回填覆盖
        _write_runtime(
            self.root,
            stage="regression",
            operation_type="bugfix",
            operation_target="bugfix-6",
            current_requirement="bugfix-6",
        )
        runtime = load_requirement_runtime(self.root)
        self.assertEqual(runtime.get("operation_type"), "bugfix")
        self.assertEqual(runtime.get("operation_target"), "bugfix-6")


if __name__ == "__main__":
    unittest.main()
