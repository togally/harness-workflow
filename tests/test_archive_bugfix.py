"""Unit tests for `archive_requirement` 的 bugfix 分流（req-28 / chg-03，AC-14）。

覆盖：
- ``archive_requirement`` 识别 ``bugfix-*`` 前缀，归档到
  ``artifacts/{branch}/archive/bugfixes/<dir>``；
- 非 done 的 bugfix 默认拒绝归档，``--force-done`` 可绕过；
- ``list_done_requirements`` 同时收入 bugfixes 下 stage==done 的条目；
- ``current_requirement`` 不是被归档 id 时，归档 bugfix 不应意外切走
  （保护主 requirement）。

Helper 层直接调用 ``archive_requirement``，不跑真 CLI（briefing 硬约束）。
tempdir 隔离；monkey-patch ``_get_git_branch`` 固定为 ``main``；patch ``input``
避免 Git auto-commit 交互。
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


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
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
    current_requirement: str = "",
    active_ids: list[str] | None = None,
) -> None:
    active_ids = active_ids or []
    lines = [
        'operation_type: "requirement"',
        'operation_target: ""',
        f'current_requirement: "{current_requirement}"',
        'stage: "done"',
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


def _seed_requirement_state(
    root: Path, req_id: str, slug: str, title: str, stage: str = "done"
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
                'status: "active"',
                'created_at: "2026-04-19"',
                'started_at: "2026-04-19"',
                'completed_at: "2026-04-19"',
                "stage_timestamps: {}",
                'description: ""',
                "",
            ]
        ),
    )
    return state_path


class ArchiveBugfixTest(unittest.TestCase):
    """AC-14：`harness archive` 支持 bugfix 分流 + --force-done。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-archive-bugfix-"))
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

    # -------- Test 1 --------
    def test_archive_bugfix_moves_dir_and_updates_runtime(self) -> None:
        """stage=done 的 bugfix 应落到 archive/bugfixes/ 且 runtime 被清理。

        同时核对 current_requirement=req-28（非被归档 id）不被切走——
        保护主需求在 sweep 期间不漂移。
        """
        from harness_workflow.workflow_helpers import archive_requirement

        folder_name = "bugfix-99-demo-archive"
        _seed_bugfix_dir(self.root, folder_name)
        _seed_bugfix_state(self.root, "bugfix-99", "demo-archive", "Demo Bugfix", stage="done")
        _write_runtime(
            self.root,
            current_requirement="req-28",
            active_ids=["bugfix-99", "req-28"],
        )

        rc = archive_requirement(self.root, "bugfix-99")
        self.assertEqual(rc, 0)

        archive_root = self.root / "artifacts" / "main" / "archive"
        expected_target = archive_root / "bugfixes" / folder_name
        self.assertTrue(
            expected_target.exists(),
            f"bugfix 归档目标应在 {expected_target.relative_to(self.root).as_posix()}; "
            f"实际树: {[p.relative_to(self.root).as_posix() for p in archive_root.rglob('*')]}",
        )
        # 归档目录内应含 state.yaml（从 state/bugfixes/ 迁入）
        self.assertTrue(
            (expected_target / "state.yaml").exists(),
            "归档目录应含 state.yaml",
        )
        # 不得落到 requirements 子树
        wrong_target = archive_root / "requirements" / folder_name
        self.assertFalse(wrong_target.exists(), "bugfix 不得落到 requirements/ 子树")
        # 不得出现双层 branch
        double_branch = archive_root / "main"
        self.assertFalse(
            double_branch.exists(),
            f"不得产生双层 branch {double_branch.relative_to(self.root).as_posix()}",
        )

        # 源目录已移走
        src_dir = self.root / "artifacts" / "main" / "bugfixes" / folder_name
        self.assertFalse(src_dir.exists(), "源 bugfix 目录应已移走")

        # runtime active_requirements 应清理掉 bugfix-99，保留 req-28
        from harness_workflow.workflow_helpers import load_requirement_runtime

        runtime = load_requirement_runtime(self.root)
        self.assertNotIn("bugfix-99", runtime.get("active_requirements", []))
        self.assertIn("req-28", runtime.get("active_requirements", []))
        # current_requirement 不被切走
        self.assertEqual(runtime.get("current_requirement"), "req-28")

        # state yaml 已迁出 .workflow/state/bugfixes/
        src_yaml = (
            self.root
            / ".workflow"
            / "state"
            / "bugfixes"
            / "bugfix-99-demo-archive.yaml"
        )
        self.assertFalse(src_yaml.exists(), "state/bugfixes/ 下 yaml 应已移走")

    # -------- Test 2 --------
    def test_archive_refuses_non_done_bugfix_without_force(self) -> None:
        """stage != done 的 bugfix，未加 --force-done 时必须报错。"""
        from harness_workflow.workflow_helpers import archive_requirement

        folder_name = "bugfix-98-active-bf"
        _seed_bugfix_dir(self.root, folder_name)
        _seed_bugfix_state(
            self.root, "bugfix-98", "active-bf", "Active BF", stage="acceptance"
        )
        _write_runtime(
            self.root,
            current_requirement="req-28",
            active_ids=["bugfix-98", "req-28"],
        )

        with self.assertRaises(SystemExit) as ctx:
            archive_requirement(self.root, "bugfix-98")
        self.assertIn("not 'done'", str(ctx.exception))

        # 源目录不得被移走
        src_dir = self.root / "artifacts" / "main" / "bugfixes" / folder_name
        self.assertTrue(src_dir.exists(), "失败路径下源 bugfix 目录应保留")
        # 归档目录不应创建子项
        archive_target = (
            self.root / "artifacts" / "main" / "archive" / "bugfixes" / folder_name
        )
        self.assertFalse(archive_target.exists())

    # -------- Test 3 --------
    def test_archive_force_done_bypasses_stage_check(self) -> None:
        """stage=regression 时，--force-done 应强置为 done 并归档成功。"""
        from harness_workflow.workflow_helpers import (
            archive_requirement,
            load_requirement_runtime,
        )

        folder_name = "bugfix-97-force-done-bf"
        _seed_bugfix_dir(self.root, folder_name)
        _seed_bugfix_state(
            self.root, "bugfix-97", "force-done-bf", "Force BF", stage="regression"
        )
        _write_runtime(
            self.root,
            current_requirement="req-28",
            active_ids=["bugfix-97", "req-28"],
        )

        rc = archive_requirement(self.root, "bugfix-97", force_done=True)
        self.assertEqual(rc, 0)

        expected_target = (
            self.root / "artifacts" / "main" / "archive" / "bugfixes" / folder_name
        )
        self.assertTrue(expected_target.exists())
        # state.yaml 随目录迁入归档；核对内容已 force 为 done+archived
        archived_state_path = expected_target / "state.yaml"
        self.assertTrue(archived_state_path.exists())
        text = archived_state_path.read_text(encoding="utf-8")
        self.assertIn('stage: "done"', text)
        self.assertIn('status: "archived"', text)  # archive 流程最终把 status 打成 archived

        runtime = load_requirement_runtime(self.root)
        self.assertNotIn("bugfix-97", runtime.get("active_requirements", []))
        self.assertIn("req-28", runtime.get("active_requirements", []))
        self.assertEqual(runtime.get("current_requirement"), "req-28")

    # -------- Test 4 --------
    def test_list_done_includes_bugfixes(self) -> None:
        """list_done_requirements 应同时收入 requirements / bugfixes 下 stage==done 的条目。"""
        from harness_workflow.workflow_helpers import list_done_requirements

        # 1 个 done requirement + 1 个 done bugfix + 1 个 active bugfix（应被过滤）
        _seed_requirement_state(self.root, "req-50", "done-req", "Done Req", stage="done")
        _seed_bugfix_state(self.root, "bugfix-51", "done-bf", "Done BF", stage="done")
        _seed_bugfix_state(
            self.root, "bugfix-52", "active-bf", "Active BF", stage="executing"
        )

        results = list_done_requirements(self.root)
        ids = {r["req_id"]: r for r in results}
        self.assertIn("req-50", ids, f"req-50 应在 done 列表中；实际: {list(ids.keys())}")
        self.assertIn(
            "bugfix-51", ids, f"bugfix-51 应在 done 列表中；实际: {list(ids.keys())}"
        )
        self.assertNotIn("bugfix-52", ids, "stage!=done 的 bugfix 不应出现")

        # kind 标签正确
        self.assertEqual(ids["req-50"].get("kind"), "req")
        self.assertEqual(ids["bugfix-51"].get("kind"), "bugfix")


if __name__ == "__main__":
    unittest.main()
