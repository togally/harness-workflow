"""Subagent-L1 独立测试补丁（req-28，测试工程师视角）。

与 chg-01~07 的自测互补，针对以下潜在漏测做独立断言：

- AC-12：懒回填在 5 次 save/load round-trip 后仍稳定保留（原 test_bugfix_runtime
  只跑 2 次）。
- AC-14：`--force-done` 对 stage=done 的 bugfix 也应幂等归档（原 test_archive_bugfix
  只覆盖 stage=regression → force-done 的场景）。
- AC-15：`create_suggestion` 在 archive 与当前目录同时存在多档历史（4+ 条混合
  编号）时仍取全集最大值 +1，原 test_suggest_cli 只覆盖单档 sug-20 场景。

硬约束：
- 不改 chg-01~07 功能代码；
- 不跑真 CLI；tempdir 隔离；monkey-patch `_get_git_branch`。
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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_harness_workspace(tmpdir: Path) -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write_runtime_bugfix(
    root: Path,
    *,
    stage: str = "regression",
    operation_type: str = "bugfix",
    operation_target: str = "bugfix-42",
    current_requirement: str = "bugfix-42",
    active_ids: list[str] | None = None,
) -> None:
    active_ids = active_ids or ["bugfix-42"]
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


def _seed_bugfix_dir(root: Path, folder_name: str) -> Path:
    bx_dir = root / "artifacts" / "main" / "bugfixes" / folder_name
    bx_dir.mkdir(parents=True, exist_ok=True)
    (bx_dir / "bugfix.md").write_text(
        f"# {folder_name}\n\nseed bugfix content\n", encoding="utf-8"
    )
    return bx_dir


def _seed_bugfix_state(
    root: Path,
    bugfix_id: str,
    slug: str,
    title: str,
    *,
    stage: str = "done",
) -> Path:
    status = "done" if stage == "done" else "active"
    completed = '"2026-04-19"' if stage == "done" else '""'
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
                'created_at: "2026-04-19"',
                'started_at: "2026-04-19"',
                f"completed_at: {completed}",
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


class LazyBackfillPersistsAcrossManyRoundTripsTest(unittest.TestCase):
    """AC-12 补测：5 次 save/load 后 operation_type 仍稳定。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req28-indep-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_operation_type_survives_five_round_trips(self) -> None:
        """save → load 连续 5 次，字段不能被任何一次裁剪丢失。"""
        from harness_workflow.workflow_helpers import (
            load_requirement_runtime,
            save_requirement_runtime,
        )

        _write_runtime_bugfix(
            self.root,
            stage="regression",
            operation_type="bugfix",
            operation_target="bugfix-42",
            current_requirement="bugfix-42",
            active_ids=["bugfix-42"],
        )

        for i in range(5):
            runtime = load_requirement_runtime(self.root)
            self.assertEqual(
                runtime.get("operation_type"),
                "bugfix",
                msg=f"round-trip #{i}: operation_type 丢失，{runtime!r}",
            )
            self.assertEqual(runtime.get("operation_target"), "bugfix-42")
            # 不改字段，原样写回
            save_requirement_runtime(self.root, runtime)

        # 最后再核对文件字面是否仍含这两行
        text = (self.root / ".workflow" / "state" / "runtime.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('operation_type: "bugfix"', text)
        self.assertIn('operation_target: "bugfix-42"', text)


class ForceDoneIdempotentOnDoneBugfixTest(unittest.TestCase):
    """AC-14 补测：--force-done 对 stage=done 的 bugfix 也应成功归档（幂等）。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req28-indep-"))
        self.root = _make_harness_workspace(self.tempdir)
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_force_done_on_already_done_bugfix_archives_successfully(self) -> None:
        """stage=done 的 bugfix 加 --force-done，归档不报错且路径正确。"""
        from harness_workflow.workflow_helpers import (
            archive_requirement,
            load_requirement_runtime,
        )

        folder_name = "bugfix-77-already-done"
        _seed_bugfix_dir(self.root, folder_name)
        _seed_bugfix_state(
            self.root, "bugfix-77", "already-done", "Already Done BF", stage="done"
        )
        _write_runtime_bugfix(
            self.root,
            stage="done",
            operation_type="requirement",
            operation_target="",
            current_requirement="req-28",
            active_ids=["bugfix-77", "req-28"],
        )

        rc = archive_requirement(self.root, "bugfix-77", force_done=True)
        self.assertEqual(rc, 0, "force-done 对 done 的 bugfix 应幂等成功")

        expected = (
            self.root
            / "artifacts"
            / "main"
            / "archive"
            / "bugfixes"
            / folder_name
        )
        self.assertTrue(expected.exists(), f"归档目标应存在：{expected}")
        self.assertTrue((expected / "state.yaml").exists())

        runtime = load_requirement_runtime(self.root)
        self.assertNotIn("bugfix-77", runtime.get("active_requirements", []))
        self.assertIn("req-28", runtime.get("active_requirements", []))


class SuggestNumberingMonotonicAcrossMixedHistoryTest(unittest.TestCase):
    """AC-15 补测：archive + 当前目录混合多档历史，仍取全集最大 +1。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req28-indep-"))
        self.root = _make_harness_workspace(self.tempdir)
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            "\n".join(
                [
                    'operation_type: "requirement"',
                    'operation_target: ""',
                    'current_requirement: ""',
                    'stage: "done"',
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
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_next_number_is_global_max_plus_one(self) -> None:
        """current: sug-05 / sug-10; archive: sug-03, sug-20, sug-15 → 新建必须 sug-21。"""
        from harness_workflow.workflow_helpers import create_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        archive_dir = sug_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)

        (sug_dir / "sug-05-current-low.md").write_text(
            "---\nid: sug-05\nstatus: pending\n---\n\n当前低编号。\n",
            encoding="utf-8",
        )
        (sug_dir / "sug-10-current-mid.md").write_text(
            "---\nid: sug-10\nstatus: pending\n---\n\n当前中编号。\n",
            encoding="utf-8",
        )
        (archive_dir / "sug-03-old-low.md").write_text(
            "---\nid: sug-03\nstatus: archived\n---\n\n历史低编号。\n",
            encoding="utf-8",
        )
        (archive_dir / "sug-20-old-high.md").write_text(
            "---\nid: sug-20\nstatus: archived\n---\n\n历史最高编号。\n",
            encoding="utf-8",
        )
        (archive_dir / "sug-15-old-mid.md").write_text(
            "---\nid: sug-15\nstatus: archived\n---\n\n历史中编号。\n",
            encoding="utf-8",
        )

        rc = create_suggestion(self.root, "req-28 独立测试 跨源取全集最大")
        self.assertEqual(rc, 0)

        new_files = sorted(
            p for p in sug_dir.glob("sug-*.md") if p.stem not in ("sug-05-current-low", "sug-10-current-mid")
        )
        self.assertEqual(
            len(new_files), 1, f"应新建 1 条 sug，实际 {new_files}"
        )
        created = new_files[0].name
        self.assertTrue(
            created.startswith("sug-21-"),
            f"新建 sug 应为 sug-21（全集 max=20 +1），实际 {created}",
        )


if __name__ == "__main__":
    unittest.main()
