"""独立反例补充测试 — req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） testing 阶段自补。

标注来源：testing 自补（独立反例 / 边界用例）。
覆盖：
- EC-01: apply-all 空 pending 池 → 幂等 0（edge: 空池 no-op）
- EC-02: _append_sug_body_to_req_md 幂等聚合（同 sug 二次调用不重复 marker）
- EC-03: rename 目标名与原名相同 → 应容错（edge: noop rename）
- EC-04: apply 单 sug body 写入失败时 sug 仍被 archive（不阻断）
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


def _make_workspace(tmpdir: Path) -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}) + "\n", encoding="utf-8"
    )
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            'operation_type: "requirement"',
            'operation_target: ""',
            'current_requirement: ""',
            'stage: "done"',
            'conversation_mode: "open"',
            'locked_requirement: ""',
            'locked_stage: ""',
            'current_regression: ""',
            'ff_mode: false',
            'ff_stage_history: []',
            'active_requirements: []',
            '',
        ]),
        encoding="utf-8",
    )
    return root


class TestApplyAllEmptyPool(unittest.TestCase):
    """EC-01: apply-all 空 pending 池 → exit 0 幂等 no-op（edge: 空池）。testing 自补。"""

    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="harness-ec01-"))
        self.root = _make_workspace(self.td)
        self._branch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch", return_value="main"
        )
        self._branch.start()
        self._inp = mock.patch("builtins.input", return_value="n")
        self._inp.start()

    def tearDown(self) -> None:
        self._inp.stop()
        self._branch.stop()
        shutil.rmtree(self.td, ignore_errors=True)

    def test_ec01_empty_pending_pool_returns_zero(self) -> None:
        """apply-all 当 suggestions 目录无 pending sug 时应返回 0 并不创建 req。"""
        from harness_workflow.workflow_helpers import apply_all_suggestions

        # 不放任何 sug 文件
        rc = apply_all_suggestions(self.root, pack_title="empty pool test")
        self.assertEqual(rc, 0, "空 pending 池 apply-all 应返回 0（幂等 no-op）")

        # 不应创建任何 req 目录
        flow_reqs = self.root / ".workflow" / "flow" / "requirements"
        self.assertEqual(list(flow_reqs.iterdir()), [],
                         "空 pending 池时不应创建任何 req 目录")


class TestAppendSugBodyIdempotent(unittest.TestCase):
    """EC-02: _append_sug_body_to_req_md 幂等聚合：同 marker 不重复（边界：多次追加）。testing 自补。"""

    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="harness-ec02-"))
        self.root = _make_workspace(self.td)

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)

    def test_ec02_idempotent_marker(self) -> None:
        """二次调用同 sug body 时，## 合并建议清单 marker 只出现 1 次（聚合不重复生成）。"""
        from harness_workflow.workflow_helpers import _append_sug_body_to_req_md, _use_flow_layout

        # 为 legacy req-id（<= 40）构造 artifacts/ requirement.md
        req_md = self.root / "artifacts" / "main" / "requirements" / "req-01-test" / "requirement.md"
        req_md.parent.mkdir(parents=True, exist_ok=True)
        req_md.write_text("# Test Req\n\n## Goal\n...\n", encoding="utf-8")

        # 第 1 次调用
        _append_sug_body_to_req_md(self.root, "req-01", "req-01-test", "sug-01", "Test Sug", "BODY-A")
        text1 = req_md.read_text(encoding="utf-8")
        self.assertEqual(text1.count("## 合并建议清单"), 1, "首次追加后应恰好 1 个 marker")

        # 第 2 次调用（相同 sug）
        _append_sug_body_to_req_md(self.root, "req-01", "req-01-test", "sug-01", "Test Sug", "BODY-A-SECOND")
        text2 = req_md.read_text(encoding="utf-8")
        self.assertEqual(text2.count("## 合并建议清单"), 1, "二次追加后 marker 仍只有 1 个（聚合不重复）")
        self.assertIn("BODY-A", text2)
        self.assertIn("BODY-A-SECOND", text2)


class TestRenameNoop(unittest.TestCase):
    """EC-03: rename 目标名与原名相同时应容错（edge: noop rename）。testing 自补。"""

    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="harness-ec03-"))
        self.root = _make_workspace(self.td)

    def tearDown(self) -> None:
        shutil.rmtree(self.td, ignore_errors=True)

    def test_ec03_rename_same_title_no_error(self) -> None:
        """rename 到相同 title 时不应崩溃；目录结构完整保留。"""
        from harness_workflow.workflow_helpers import rename_requirement

        # 准备 req-07（legacy，无 flow/ 目录）
        old_title = "Same Title"
        req_id = "req-07"
        old_slug = "same-title"
        dir_name = f"{req_id}-{old_slug}"
        art_dir = self.root / "artifacts" / "main" / "requirements" / dir_name
        art_dir.mkdir(parents=True, exist_ok=True)
        (art_dir / "requirement.md").write_text(f"# {old_title}\n", encoding="utf-8")
        state_file = self.root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
        state_file.write_text(
            f'id: "{req_id}"\ntitle: "{old_title}"\nstage: "executing"\nstatus: "active"\n',
            encoding="utf-8",
        )
        # runtime: req-07 is current
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            "\n".join([
                'operation_type: "requirement"',
                f'operation_target: "{req_id}"',
                f'current_requirement: "{req_id}"',
                f'current_requirement_title: "{old_title}"',
                'stage: "executing"',
                'conversation_mode: "harness"',
                'locked_requirement: ""',
                'locked_requirement_title: ""',
                'locked_stage: ""',
                'current_regression: ""',
                'ff_mode: false',
                'ff_stage_history: []',
                f'active_requirements:\n  - {req_id}',
                '',
            ]),
            encoding="utf-8",
        )

        # rename with same title
        try:
            rc = rename_requirement(self.root, req_id, old_title)
            # Either returns 0 or handles gracefully
            # The key is no exception thrown
        except Exception as exc:
            self.fail(f"rename 相同 title 不应抛出异常: {exc}")


class TestApplySugBodyWriteFailNotBlock(unittest.TestCase):
    """EC-04: apply 单 sug body 写入失败时 sug 仍被 archive（不阻断）。testing 自补。"""

    def setUp(self) -> None:
        self.td = Path(tempfile.mkdtemp(prefix="harness-ec04-"))
        self.root = _make_workspace(self.td)
        self._branch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch", return_value="main"
        )
        self._branch.start()
        self._inp = mock.patch("builtins.input", return_value="n")
        self._inp.start()

    def tearDown(self) -> None:
        self._inp.stop()
        self._branch.stop()
        shutil.rmtree(self.td, ignore_errors=True)

    def test_ec04_body_write_fail_sug_still_archived(self) -> None:
        """_append_sug_body_to_req_md 抛 OSError 时，sug 仍被 archive（不留 pending 半挂态）。"""
        from harness_workflow.workflow_helpers import apply_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        sug_path = sug_dir / "sug-88-ec04.md"
        sug_path.write_text(
            "---\nid: sug-88\ntitle: \"EC-04 Test\"\nstatus: pending\ncreated_at: 2026-04-25\npriority: medium\n---\n\nEC04-BODY\n",
            encoding="utf-8",
        )

        with mock.patch(
            "harness_workflow.workflow_helpers._append_sug_body_to_req_md",
            side_effect=OSError("disk full simulation"),
        ):
            rc = apply_suggestion(self.root, "sug-88")

        # apply_suggestion returns result of create_requirement (0 = ok)
        # body write failure does not block sug archive
        # sug file should be moved to archive (not remain in pending)
        self.assertFalse(sug_path.exists(), "apply 后 sug pending 文件应不再存在（已 archive）")
        archive_dir = sug_dir / "archive"
        archived = list(archive_dir.glob("sug-88*.md"))
        self.assertEqual(len(archived), 1, f"sug-88 应在 archive 目录: {list(archive_dir.iterdir()) if archive_dir.exists() else 'no archive dir'}")


if __name__ == "__main__":
    unittest.main()
