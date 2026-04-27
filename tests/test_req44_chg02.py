"""Tests for req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） / chg-02（rename CLI 同步范围扩展）.

覆盖 plan.md §4 测试用例 TC-01 ~ TC-05：
- TC-01: rename 同步 .workflow/flow/ 目录
- TC-02: rename 同步 runtime current_requirement_title
- TC-03: rename 同步 runtime locked_requirement_title
- TC-04: rename 不命中 current 时不动 runtime title
- TC-05: rename legacy req-id（无 flow/ 目录）兼容
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
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return root


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _seed_req_all_three(
    root: Path,
    req_id: str,
    old_slug: str,
    title: str,
    *,
    with_flow_dir: bool = True,
    make_current: bool = False,
    make_locked: bool = False,
) -> dict:
    """Seed requirement in all three locations: artifacts/, state/, and optionally flow/."""
    dir_name = f"{req_id}-{old_slug}"
    # artifacts/
    req_dir = root / "artifacts" / "main" / "requirements" / dir_name
    _write(req_dir / "meta.yaml", f'id: "{req_id}"\ntitle: "{title}"\n')
    _write(req_dir / "requirement.md", f"# {title}\n\n## Goal\n...\n")
    # state/
    _write(
        root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml",
        "\n".join([f'id: "{req_id}"', f'title: "{title}"', 'stage: "executing"', 'status: "active"', ""]),
    )
    # flow/
    if with_flow_dir:
        flow_dir = root / ".workflow" / "flow" / "requirements" / dir_name
        _write(flow_dir / "requirement.md", f"# {title}\n")

    # runtime
    runtime_lines = [
        f'operation_type: "requirement"',
        f'operation_target: "{req_id}"',
    ]
    if make_current:
        runtime_lines += [
            f'current_requirement: "{req_id}"',
            f'current_requirement_title: "{title}"',
        ]
    else:
        runtime_lines += [
            'current_requirement: "req-99"',
            'current_requirement_title: "other req"',
        ]
    if make_locked:
        runtime_lines += [
            f'locked_requirement: "{req_id}"',
            f'locked_requirement_title: "{title}"',
        ]
    else:
        runtime_lines += [
            'locked_requirement: ""',
            'locked_requirement_title: ""',
        ]
    runtime_lines += [
        'stage: "executing"',
        'conversation_mode: "harness"',
        'locked_stage: ""',
        'current_regression: ""',
        'ff_mode: false',
        'ff_stage_history: []',
        f'active_requirements:\n  - {req_id}',
        "",
    ]
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(runtime_lines), encoding="utf-8"
    )

    return {"req_id": req_id, "dir_name": dir_name}


class TestRenameReqFlowSync(unittest.TestCase):
    """TC-01: rename 同步 .workflow/flow/ 目录."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-chg02-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_tc01_rename_syncs_flow_dir(self) -> None:
        """TC-01: rename req-id >= 41 syncs flow/, artifacts/, state/ all three dirs."""
        from harness_workflow.workflow_helpers import rename_requirement

        _seed_req_all_three(self.root, "req-41", "old-title", "Old Title", with_flow_dir=True, make_current=True)

        rc = rename_requirement(self.root, "req-41", "New Title Flow")
        self.assertEqual(rc, 0)

        # artifacts/ renamed
        art_dir = self.root / "artifacts" / "main" / "requirements"
        art_names = [d.name for d in art_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(art_names), 1)
        self.assertTrue(art_names[0].startswith("req-41-"), f"unexpected: {art_names}")
        self.assertNotIn("req-41-old-title", art_names)

        # flow/ renamed
        flow_dir = self.root / ".workflow" / "flow" / "requirements"
        flow_names = [d.name for d in flow_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(flow_names), 1)
        self.assertTrue(flow_names[0].startswith("req-41-"), f"flow unexpected: {flow_names}")
        self.assertNotIn("req-41-old-title", flow_names, "旧 flow/ 目录应不存在")

        # state yaml renamed
        state_dir = self.root / ".workflow" / "state" / "requirements"
        state_names = [p.name for p in state_dir.iterdir() if p.is_file()]
        self.assertNotIn("req-41-old-title.yaml", state_names)
        new_art = art_names[0]
        self.assertIn(f"{new_art}.yaml", state_names)


class TestRenameRuntimeCurrentTitle(unittest.TestCase):
    """TC-02: rename 同步 runtime current_requirement_title."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-cur-title-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_tc02_rename_syncs_current_requirement_title(self) -> None:
        """TC-02: rename 当前 active req → runtime current_requirement_title 更新."""
        from harness_workflow.workflow_helpers import rename_requirement, load_requirement_runtime

        _seed_req_all_three(self.root, "req-41", "old-cur", "Old Current", with_flow_dir=True, make_current=True)

        rc = rename_requirement(self.root, "req-41", "New Current Title")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        self.assertEqual(str(runtime.get("current_requirement", "")), "req-41", "req id 应不变")
        cur_title = str(runtime.get("current_requirement_title", ""))
        self.assertIn("New Current Title", cur_title, f"current_requirement_title 应更新, 实际: {cur_title}")


class TestRenameRuntimeLockedTitle(unittest.TestCase):
    """TC-03: rename 同步 runtime locked_requirement_title."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-locked-title-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_tc03_rename_syncs_locked_requirement_title(self) -> None:
        """TC-03: conversation_mode=harness + locked_requirement 命中 → locked_requirement_title 更新."""
        from harness_workflow.workflow_helpers import rename_requirement, load_requirement_runtime

        _seed_req_all_three(
            self.root, "req-41", "old-locked", "Old Locked",
            with_flow_dir=True, make_current=True, make_locked=True
        )

        rc = rename_requirement(self.root, "req-41", "New Locked Title")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        locked_title = str(runtime.get("locked_requirement_title", ""))
        self.assertIn("New Locked Title", locked_title, f"locked_requirement_title 应更新, 实际: {locked_title}")


class TestRenameNoCurrentNothing(unittest.TestCase):
    """TC-04: rename 不命中 current 时不动 runtime current/locked title."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-no-cur-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_tc04_rename_non_current_does_not_touch_runtime_title(self) -> None:
        """TC-04: rename 非 current_requirement 的旧 req → runtime title 字段保持原值."""
        from harness_workflow.workflow_helpers import rename_requirement, load_requirement_runtime

        # make_current=False: current_requirement will be "req-99"
        _seed_req_all_three(self.root, "req-41", "old-non-cur", "Old Non Current",
                            with_flow_dir=True, make_current=False)

        runtime_before = load_requirement_runtime(self.root)
        cur_title_before = str(runtime_before.get("current_requirement_title", ""))

        rc = rename_requirement(self.root, "req-41", "New Non Current Title")
        self.assertEqual(rc, 0)

        runtime_after = load_requirement_runtime(self.root)
        cur_title_after = str(runtime_after.get("current_requirement_title", ""))
        # current_requirement is req-99, not req-41; title should NOT change
        self.assertEqual(cur_title_before, cur_title_after,
            f"非 current req rename 不应改 current_requirement_title: {cur_title_before!r} -> {cur_title_after!r}")


class TestRenameLegacyNoFlowDir(unittest.TestCase):
    """TC-05: rename legacy req-id（无 flow/ 目录）兼容."""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-req44-legacy-"))
        self.root = _make_harness_workspace(self.tempdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_tc05_rename_legacy_req_no_flow_dir(self) -> None:
        """TC-05: req-id <= 40 without flow/ dir → exit 0, only artifacts/ + state/ renamed, no error."""
        from harness_workflow.workflow_helpers import rename_requirement

        # with_flow_dir=False: simulate legacy req with no flow/ dir
        _seed_req_all_three(self.root, "req-07", "old-legacy", "Old Legacy",
                            with_flow_dir=False, make_current=True)

        rc = rename_requirement(self.root, "req-07", "New Legacy Title")
        self.assertEqual(rc, 0, "legacy req rename 应返回 0")

        # artifacts/ renamed
        art_dir = self.root / "artifacts" / "main" / "requirements"
        art_names = [d.name for d in art_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(art_names), 1)
        self.assertTrue(art_names[0].startswith("req-07-"), f"unexpected: {art_names}")
        self.assertNotIn("req-07-old-legacy", art_names)

        # flow/ should still be empty (no dir was created)
        flow_dir = self.root / ".workflow" / "flow" / "requirements"
        flow_names = [d.name for d in flow_dir.iterdir() if d.is_dir()]
        self.assertEqual(len(flow_names), 0, "flow/ 不应有任何目录（legacy req 无 flow/ 目录）")


if __name__ == "__main__":
    unittest.main()
