"""Tests for req-41（机器型工件回 flow/requirements）/ chg-02（CLI 路径迁移 flow layout）.

覆盖：
- _use_flow_layout helper（AC-03）
- create_requirement flow 路径（AC-04）
- create_change flow 路径（AC-04）
- create_regression flow 路径（AC-04）
- archive_requirement flow 路径（AC-05）
- 回归不破坏：req-39/40 行为不变（AC-06）
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _init_harness_repo_flow(root: Path, req_id: str, req_title: str = "flow test req") -> Path:
    """Create minimal harness repo with flow layout structure for req-id >= 41."""
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join([
            f'current_requirement: "{req_id}"',
            f'current_requirement_title: "{req_title}"',
            'stage: "planning"',
            'operation_type: "requirement"',
            f'operation_target: "{req_id}"',
            'conversation_mode: "open"',
            f'active_requirements: ["{req_id}"]',
            "",
        ]),
        encoding="utf-8",
    )
    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    return root / ".workflow" / "flow" / "requirements" / dir_name


def _init_harness_repo_flow_with_req_created(root: Path, req_id: str, req_title: str = "flow test req") -> Path:
    """Create minimal harness repo and call create_requirement, returning the flow req dir."""
    _init_harness_repo_flow(root, req_id, req_title)
    from harness_workflow.workflow_helpers import create_requirement
    create_requirement(root, None, requirement_id=req_id, title=req_title)

    from harness_workflow.slug import slugify_preserve_unicode
    slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
    dir_name = f"{req_id}-{slug}"
    return root / ".workflow" / "flow" / "requirements" / dir_name


# ---------------------------------------------------------------------------
# AC-03: _use_flow_layout helper
# ---------------------------------------------------------------------------

class UseFlowLayoutHelperTest(unittest.TestCase):
    """req-41 / chg-02 AC-03: _use_flow_layout helper boundary tests."""

    def test_use_flow_layout_req_40_false(self) -> None:
        """req-40 → False（state-flat 路径，不是 flow 路径）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertFalse(_use_flow_layout("req-40"), "req-40 应走 state-flat 路径，不走 flow")

    def test_use_flow_layout_req_41_true(self) -> None:
        """req-41 → True（flow 路径起点）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertTrue(_use_flow_layout("req-41"), "req-41 应走 flow 路径")

    def test_use_flow_layout_req_50_true(self) -> None:
        """req-50 → True（flow 路径，高 id 也成立）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertTrue(_use_flow_layout("req-50"), "req-50 应走 flow 路径")

    def test_use_flow_layout_invalid_id_false_empty(self) -> None:
        """空串 → False."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertFalse(_use_flow_layout(""), "空 id 应返回 False")

    def test_use_flow_layout_invalid_id_false_none_equiv(self) -> None:
        """None → False（仅能通过空串测试，因 type hint 是 str，用 '' 替代）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        # None 不可传入（类型不符），改用空字符串覆盖 null-like 场景
        self.assertFalse(_use_flow_layout(""), "空串（null-like）应返回 False")

    def test_use_flow_layout_invalid_id_false_abc(self) -> None:
        """'abc' → False（非 req-\\d+ 形式）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertFalse(_use_flow_layout("abc"), "非 req-\\d+ 形式应返回 False")

    def test_use_flow_layout_invalid_id_false_req_abc(self) -> None:
        """'req-abc' → False（数字部分为非数字）."""
        from harness_workflow.workflow_helpers import _use_flow_layout
        self.assertFalse(_use_flow_layout("req-abc"), "req-abc 应返回 False")

    def test_use_flow_layout_implies_flat_layout(self) -> None:
        """flow(x) → True 蕴含 flat(x) → True（flow ⊂ flat 语义保证）."""
        from harness_workflow.workflow_helpers import _use_flow_layout, _use_flat_layout
        for req_id in ["req-41", "req-50", "req-99"]:
            self.assertTrue(_use_flow_layout(req_id), f"{req_id} 应走 flow 路径")
            self.assertTrue(_use_flat_layout(req_id), f"{req_id} 同时应走 flat 路径（flow ⊂ flat）")

    def test_flow_layout_constant_is_41(self) -> None:
        """FLOW_LAYOUT_FROM_REQ_ID 常量值为 41."""
        from harness_workflow.workflow_helpers import FLOW_LAYOUT_FROM_REQ_ID
        self.assertEqual(FLOW_LAYOUT_FROM_REQ_ID, 41)


# ---------------------------------------------------------------------------
# AC-04: create_requirement flow 路径
# ---------------------------------------------------------------------------

class CreateRequirementFlowLayoutTest(unittest.TestCase):
    """req-41 / chg-02 AC-04: create_requirement flow 路径断言."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_requirement_flow_layout_req_41(self) -> None:
        """req-id = 41: requirement.md 落 .workflow/flow/requirements/req-41-{slug}/requirement.md."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_flow(self.root, "req-41")
        rc = create_requirement(self.root, None, requirement_id="req-41", title="flow req test")
        self.assertEqual(rc, 0)

        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-41-*"))
        self.assertTrue(req_dirs, "flow requirements/ 下应存在 req-41-* 目录")
        req_md = req_dirs[0] / "requirement.md"
        self.assertTrue(
            req_md.exists(),
            f"requirement.md 应落在 flow requirements 目录 {req_md}，实际不存在",
        )

    def test_create_requirement_flow_layout_not_in_state_requirements(self) -> None:
        """req-id = 41: requirement.md 不应出现在 state/requirements/ 下（flow 路径专属）."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_flow(self.root, "req-41")
        create_requirement(self.root, None, requirement_id="req-41", title="flow req not in state")

        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-41"
        self.assertFalse(
            state_req_dir.exists(),
            "flow req 的 requirement.md 不应落在 state/requirements/req-41/ 下",
        )

    def test_create_requirement_flow_layout_artifacts_dir_exists(self) -> None:
        """req-id = 41: artifacts/ 下应建根目录（对人文档占位），不建 changes/ 子目录."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_flow(self.root, "req-41")
        create_requirement(self.root, None, requirement_id="req-41", title="flow req artifacts check")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-41-*"))
        self.assertTrue(req_dirs, "artifacts/ 下应存在 req-41-* 目录（对人文档占位）")
        changes_dir = req_dirs[0] / "changes"
        self.assertFalse(changes_dir.exists(), "flow req 不应在 artifacts/ 下建 changes/ 子目录")

    def test_create_requirement_flow_layout_req_50(self) -> None:
        """req-id = 50: 同 req-41，也走 flow 路径."""
        from harness_workflow.workflow_helpers import create_requirement

        _init_harness_repo_flow(self.root, "req-50")
        rc = create_requirement(self.root, None, requirement_id="req-50", title="flow req 50 test")
        self.assertEqual(rc, 0)

        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-50-*"))
        self.assertTrue(req_dirs, "flow requirements/ 下应存在 req-50-* 目录")


# ---------------------------------------------------------------------------
# AC-04: create_change flow 路径
# ---------------------------------------------------------------------------

class CreateChangeFlowLayoutTest(unittest.TestCase):
    """req-41 / chg-02 AC-04: create_change flow 路径断言."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_change_flow_layout_req_41(self) -> None:
        """req-id = 41: change.md / plan.md 落 .workflow/flow/requirements/req-41-{slug}/changes/chg-01-{slug}/."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo_flow_with_req_created(self.root, "req-41", "flow req 41 change test")
        rc = create_change(self.root, "first flow change")
        self.assertEqual(rc, 0)

        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-41-*"))
        self.assertTrue(req_dirs, "flow requirements/ 下应存在 req-41-* 目录")
        req_dir = req_dirs[0]
        changes_dir = req_dir / "changes"
        chg_dirs = list(changes_dir.glob("chg-*"))
        self.assertTrue(chg_dirs, f"changes/ 目录必须在 {changes_dir} 下存在，实际：{list(changes_dir.iterdir()) if changes_dir.exists() else '目录不存在'}")
        chg_dir = chg_dirs[0]
        self.assertTrue((chg_dir / "change.md").exists(), "change.md 应在 flow changes/ 目录下")
        self.assertTrue((chg_dir / "plan.md").exists(), "plan.md 应在 flow changes/ 目录下")
        self.assertTrue((chg_dir / "session-memory.md").exists(), "session-memory.md 应在 flow changes/ 目录下")

    def test_create_change_flow_layout_req_41_not_in_state_sessions(self) -> None:
        """req-id = 41: .workflow/state/sessions/ 下不应创建 chg 目录（flow 路径不走 state/sessions）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo_flow_with_req_created(self.root, "req-41", "flow req 41 no state sessions")
        create_change(self.root, "flow change no state sessions")

        state_sessions = self.root / ".workflow" / "state" / "sessions" / "req-41"
        self.assertFalse(
            state_sessions.exists(),
            "flow req 不应在 state/sessions/ 下创建 chg 目录",
        )

    def test_create_change_flow_layout_req_41_no_brief_placeholder(self) -> None:
        """req-id = 41: artifacts/ 下不应创建 变更简报.md placeholder（仅 state-flat 创建 placeholder）."""
        from harness_workflow.workflow_helpers import create_change

        _init_harness_repo_flow_with_req_created(self.root, "req-41", "flow req 41 no brief")
        create_change(self.root, "flow change no brief placeholder")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-41-*"))
        if req_dirs:
            brief_files = list(req_dirs[0].glob("chg-*-变更简报.md"))
            self.assertFalse(
                brief_files,
                "flow req 不应在 artifacts/ 下创建 变更简报.md placeholder（归属 chg-03 删除）",
            )


# ---------------------------------------------------------------------------
# AC-04: create_regression flow 路径
# ---------------------------------------------------------------------------

class CreateRegressionFlowLayoutTest(unittest.TestCase):
    """req-41 / chg-02 AC-04: create_regression flow 路径断言."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def test_create_regression_flow_layout_req_41(self) -> None:
        """req-id = 41: regression 产物落 .workflow/flow/requirements/req-41-{slug}/regressions/reg-01-{slug}/."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo_flow_with_req_created(self.root, "req-41", "flow req 41 regression test")
        rc = create_regression(self.root, "flow regression issue")
        self.assertEqual(rc, 0)

        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        req_dirs = list(flow_req_base.glob("req-41-*"))
        self.assertTrue(req_dirs, "flow requirements/ 下应存在 req-41-* 目录")
        req_dir = req_dirs[0]
        reg_base = req_dir / "regressions"
        reg_dirs = list(reg_base.glob("reg-*"))
        self.assertTrue(reg_dirs, f"regressions/ 目录必须在 {reg_base} 下存在")
        reg_dir = reg_dirs[0]
        self.assertTrue((reg_dir / "regression.md").exists(), "regression.md 应在 flow regressions/ 目录下")
        self.assertTrue((reg_dir / "analysis.md").exists(), "analysis.md 应在 flow regressions/ 目录下")
        self.assertTrue((reg_dir / "decision.md").exists(), "decision.md 应在 flow regressions/ 目录下")
        self.assertTrue((reg_dir / "meta.yaml").exists(), "meta.yaml 应在 flow regressions/ 目录下")
        self.assertTrue((reg_dir / "session-memory.md").exists(), "session-memory.md 应在 flow regressions/ 目录下")

    def test_create_regression_flow_layout_req_41_not_in_state_sessions(self) -> None:
        """req-id = 41: state/sessions/ 下不应创建 regressions 目录（flow 路径不走 state/sessions）."""
        from harness_workflow.workflow_helpers import create_regression

        _init_harness_repo_flow_with_req_created(self.root, "req-41", "flow req 41 no state reg")
        create_regression(self.root, "flow regression no state sessions")

        state_reg_base = self.root / ".workflow" / "state" / "sessions" / "req-41" / "regressions"
        self.assertFalse(
            state_reg_base.exists(),
            "flow req 不应在 state/sessions/ 下创建 regressions 目录",
        )


# ---------------------------------------------------------------------------
# AC-05: archive_requirement flow 路径
# ---------------------------------------------------------------------------

class ArchiveRequirementFlowLayoutTest(unittest.TestCase):
    """req-41 / chg-02 AC-05: archive_requirement flow 路径断言."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def _setup_flow_req_for_archive(
        self,
        req_id: str = "req-41",
        req_title: str = "flow archive test",
    ) -> Path:
        """Create a flow req fully populated for archive testing. Returns flow req dir."""
        from harness_workflow.slug import slugify_preserve_unicode

        # base dirs
        (root := self.root)
        (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
        (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
        (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
        (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
        (root / ".codex" / "harness").mkdir(parents=True)
        (root / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (root / "artifacts" / "main" / "requirements").mkdir(parents=True)

        slug = slugify_preserve_unicode(req_title) or req_title.replace(" ", "-")
        dir_name = f"{req_id}-{slug}"

        # flow req dir with change + regression
        flow_req_dir = root / ".workflow" / "flow" / "requirements" / dir_name
        flow_req_dir.mkdir(parents=True)
        (flow_req_dir / "requirement.md").write_text("# Requirement\n", encoding="utf-8")
        chg_dir = flow_req_dir / "changes" / "chg-01-test-change"
        chg_dir.mkdir(parents=True)
        (chg_dir / "change.md").write_text("# Change\n", encoding="utf-8")
        reg_dir = flow_req_dir / "regressions" / "reg-01-test-reg"
        reg_dir.mkdir(parents=True)
        (reg_dir / "regression.md").write_text("# Regression\n", encoding="utf-8")

        # artifacts/ req dir（对人文档占位）
        artifacts_req_dir = root / "artifacts" / "main" / "requirements" / dir_name
        artifacts_req_dir.mkdir(parents=True)
        (artifacts_req_dir / "需求摘要.md").write_text("# 需求摘要\n", encoding="utf-8")

        # state yaml
        state_yaml = root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
        state_yaml.write_text(
            "\n".join([
                f'id: "{req_id}"',
                f'title: "{req_title}"',
                'stage: "done"',
                'status: "active"',
                "",
            ]),
            encoding="utf-8",
        )

        # runtime
        (root / ".workflow" / "state" / "runtime.yaml").write_text(
            "\n".join([
                f'current_requirement: "{req_id}"',
                f'current_requirement_title: "{req_title}"',
                'stage: "done"',
                'operation_type: "requirement"',
                f'operation_target: "{req_id}"',
                'conversation_mode: "open"',
                f'active_requirements: ["{req_id}"]',
                "",
            ]),
            encoding="utf-8",
        )
        return flow_req_dir

    def test_archive_requirement_flow_layout_req_41(self) -> None:
        """req-id = 41: 归档后 .workflow/flow/requirements/req-41-{slug}/ 整体移到 .workflow/flow/archive/{branch}/req-41-{slug}/."""
        from harness_workflow.workflow_helpers import archive_requirement

        flow_req_dir = self._setup_flow_req_for_archive("req-41", "flow archive test req 41")
        rc = archive_requirement(self.root, "req-41")
        self.assertEqual(rc, 0)

        # 源目录不存在
        self.assertFalse(
            flow_req_dir.exists(),
            f"归档后源目录 {flow_req_dir} 应不存在",
        )

        # 目标目录存在
        flow_archive_base = self.root / ".workflow" / "flow" / "archive"
        archive_dirs = list(flow_archive_base.glob("*/req-41-*"))
        self.assertTrue(
            archive_dirs,
            f"归档目录 .workflow/flow/archive/{{branch}}/req-41-* 应存在，实际：{list(flow_archive_base.rglob('*'))}",
        )
        archive_dir = archive_dirs[0]

        # 子文件齐全
        self.assertTrue((archive_dir / "requirement.md").exists(), "归档目录应含 requirement.md")
        self.assertTrue((archive_dir / "changes" / "chg-01-test-change" / "change.md").exists(), "归档目录应含 changes/ 子目录")
        self.assertTrue((archive_dir / "regressions" / "reg-01-test-reg" / "regression.md").exists(), "归档目录应含 regressions/ 子目录")

    def test_archive_requirement_flow_layout_state_sessions_not_migrated(self) -> None:
        """req-id = 41: flow req 归档不迁移 state/sessions/（内嵌于 flow 子树，无需额外迁移）."""
        from harness_workflow.workflow_helpers import archive_requirement

        self._setup_flow_req_for_archive("req-41", "flow archive state sessions check")
        archive_requirement(self.root, "req-41")

        # state/sessions/req-41/ 不应被创建（flow req 不使用 state/sessions）
        state_sessions = self.root / ".workflow" / "state" / "sessions" / "req-41"
        self.assertFalse(
            state_sessions.exists(),
            "flow req 归档时不应迁移 state/sessions/req-41/（flow 子树已含所有 sessions）",
        )


# ---------------------------------------------------------------------------
# AC-06: 回归不破坏 — req-39/40 行为不变
# ---------------------------------------------------------------------------

class FlowLayoutRegressionGuardTest(unittest.TestCase):
    """req-41 / chg-02 AC-06: req-39/40 state-flat 行为不变（回归护栏）."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"

    def _init_repo_flat(self, req_id: str, req_title: str = "flat req") -> None:
        (self.root / ".workflow" / "state" / "requirements").mkdir(parents=True)
        (self.root / ".workflow" / "state" / "sessions").mkdir(parents=True)
        (self.root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
        (self.root / ".codex" / "harness").mkdir(parents=True)
        (self.root / ".codex" / "harness" / "config.json").write_text(
            json.dumps({"language": "english"}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (self.root / "artifacts" / "main" / "requirements").mkdir(parents=True)
        (self.root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
        (self.root / ".workflow" / "state" / "runtime.yaml").write_text(
            "\n".join([
                f'current_requirement: "{req_id}"',
                f'current_requirement_title: "{req_title}"',
                'stage: "planning"',
                'operation_type: "requirement"',
                f'operation_target: "{req_id}"',
                'conversation_mode: "open"',
                f'active_requirements: ["{req_id}"]',
                "",
            ]),
            encoding="utf-8",
        )

    def test_req_40_create_requirement_still_uses_state_flat(self) -> None:
        """req-40 create_requirement 仍走 state-flat（不走 flow）."""
        from harness_workflow.workflow_helpers import create_requirement

        self._init_repo_flat("req-40", "flat req 40")
        create_requirement(self.root, None, requirement_id="req-40", title="flat req 40 guard")

        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-40"
        self.assertTrue(
            state_req_dir.exists(),
            "req-40 应走 state-flat：requirement.md 应在 state/requirements/req-40/ 下",
        )

        flow_req_base = self.root / ".workflow" / "flow" / "requirements"
        flow_dirs = list(flow_req_base.glob("req-40-*")) if flow_req_base.exists() else []
        self.assertFalse(
            flow_dirs,
            "req-40 不应在 flow/requirements/ 下创建目录",
        )

    def test_req_39_create_requirement_still_uses_state_flat(self) -> None:
        """req-39 create_requirement 仍走 state-flat（不走 flow）."""
        from harness_workflow.workflow_helpers import create_requirement

        self._init_repo_flat("req-39", "flat req 39")
        create_requirement(self.root, None, requirement_id="req-39", title="flat req 39 guard")

        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-39"
        self.assertTrue(
            state_req_dir.exists(),
            "req-39 应走 state-flat：requirement.md 应在 state/requirements/req-39/ 下",
        )

    def test_req_10_create_requirement_still_uses_legacy(self) -> None:
        """req-10 create_requirement 仍走 legacy（不走 flat 或 flow）."""
        from harness_workflow.workflow_helpers import create_requirement

        self._init_repo_flat("req-10", "legacy req 10")
        create_requirement(self.root, None, requirement_id="req-10", title="legacy req 10 guard")

        artifacts_req_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = list(artifacts_req_base.glob("req-10-*"))
        self.assertTrue(req_dirs, "legacy req 应在 artifacts/ 下建目录")
        req_md = req_dirs[0] / "requirement.md"
        self.assertTrue(req_md.exists(), "legacy req 的 requirement.md 应在 artifacts/ req 目录下")

        state_req_dir = self.root / ".workflow" / "state" / "requirements" / "req-10"
        self.assertFalse(state_req_dir.exists(), "legacy req 不应在 state/requirements/req-id/ 下建子目录")


if __name__ == "__main__":
    unittest.main()
