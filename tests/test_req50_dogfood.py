"""req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）/
chg-05（dogfood + reviewer 加项 + 端到端测试）dogfood 测试套件。

覆盖：
- TC-01：req-id ≥ 50 走 5-stage（analysis / executing / testing / acceptance / done）
- TC-02：req-id < 50 历史归档兼容旧 sequence（D5=B）
- TC-03：harness next 单入口 — analysis 末尾 stage_pending_user_action →
          harness next 推进到 executing
- TC-04：done 阶段不产 sug 入池（chg-02 落地验证）
- TC-05：渲染 5 个核心机器型模板 + 7 个验证交付模板正常
- TC-06：reviewer.md / review-checklist.md 含新加项（grep 验证）
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# 工具函数：构造最小 harness workspace
# ---------------------------------------------------------------------------


def _make_harness_workspace(tmpdir: Path, language: str = "cn") -> Path:
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "state" / "feedback").mkdir(parents=True)
    (root / ".workflow" / "flow" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "tests").mkdir(parents=True)
    # 占位 test 文件（executing gate 要求 tests/ 下至少 1 个 test_*.py）
    (root / "tests" / "test_placeholder.py").write_text(
        "# placeholder\n", encoding="utf-8"
    )
    _write_runtime(root, "", "")
    return root


def _write_runtime(
    root: Path,
    current_requirement: str,
    stage: str,
    operation_type: str = "requirement",
) -> None:
    (root / ".workflow" / "state" / "runtime.yaml").write_text(
        "\n".join(
            [
                f'operation_type: "{operation_type}"',
                f'operation_target: "{current_requirement}"',
                f'current_requirement: "{current_requirement}"',
                f'stage: "{stage}"',
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


def _get_runtime(root: Path) -> dict:
    """Load runtime.yaml as dict."""
    import yaml  # type: ignore
    return yaml.safe_load(
        (root / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8")
    ) or {}


def _create_minimal_req_state(
    root: Path, req_id: str, title: str, stage: str = "analysis"
) -> Path:
    """Create requirement state yaml and flow directory."""
    from harness_workflow.workflow_helpers import _path_slug

    slug = _path_slug(title)
    dir_name = f"{req_id}-{slug}" if slug else req_id

    # state yaml
    state_file = (
        root / ".workflow" / "state" / "requirements" / f"{dir_name}.yaml"
    )
    state_file.write_text(
        "\n".join(
            [
                f'id: "{req_id}"',
                f'title: "{title}"',
                f"stage: {stage}",
                "status: active",
                "created_at: 2026-04-29",
                "started_at: 2026-04-29",
                'completed_at: ""',
                "",
            ]
        ),
        encoding="utf-8",
    )

    # flow directory
    req_flow = root / ".workflow" / "flow" / "requirements" / dir_name
    req_flow.mkdir(parents=True, exist_ok=True)
    (req_flow / "requirement.md").write_text(
        f"---\nid: {req_id}\ntitle: \"{title}\"\ncreated_at: 2026-04-29\noperation_type: requirement\n---\n\n# {title}\n",
        encoding="utf-8",
    )
    (req_flow / "changes").mkdir(exist_ok=True)

    # runtime
    _write_runtime(root, req_id, stage)

    return req_flow


def _populate_executing_artifacts(req_flow: Path) -> None:
    """Create executing stage artifacts: chg-01/session-memory.md with ✅."""
    chg_dir = req_flow / "changes" / "chg-01-test"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text(
        "---\nreq_id: req-50\nchg_id: chg-01\nts: 2026-04-29\n---\n\n## status\ndone\n\n✅\n",
        encoding="utf-8",
    )


def _populate_testing_artifacts(req_flow: Path) -> None:
    """Create testing stage artifacts: test-report.md with §结论."""
    (req_flow / "test-report.md").write_text(
        "---\nid: test-report\ncreated_at: 2026-04-29\noperation_type: test-report\n---\n\n## §结论\nPASS\n",
        encoding="utf-8",
    )


def _populate_acceptance_artifacts(req_flow: Path) -> None:
    """Create acceptance stage artifacts: acceptance/checklist.md with §结论."""
    (req_flow / "acceptance").mkdir(exist_ok=True)
    (req_flow / "acceptance" / "checklist.md").write_text(
        "---\nid: checklist\ncreated_at: 2026-04-29\noperation_type: acceptance-checklist\n---\n\n## §结论\nPASS\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# TC-01：req-id ≥ 50 走 5-stage
# ---------------------------------------------------------------------------


class TC01NewReqFiveStageFlowTest(unittest.TestCase):
    """TC-01：req-id >= 50 使用新 5-stage（analysis / executing / testing / acceptance / done）。

    验证 _use_new_workflow_sequence 返回 True，WORKFLOW_SEQUENCE 包含 analysis。
    """

    def test_use_new_workflow_sequence_req50(self) -> None:
        from harness_workflow.workflow_helpers import _use_new_workflow_sequence

        self.assertTrue(_use_new_workflow_sequence("req-50"))
        self.assertTrue(_use_new_workflow_sequence("req-51"))
        self.assertTrue(_use_new_workflow_sequence("req-99"))

    def test_new_workflow_sequence_contains_analysis(self) -> None:
        from harness_workflow.workflow_helpers import WORKFLOW_SEQUENCE

        self.assertIn("analysis", WORKFLOW_SEQUENCE)
        # 5 stages
        self.assertEqual(
            WORKFLOW_SEQUENCE,
            ["analysis", "executing", "testing", "acceptance", "done"],
            "WORKFLOW_SEQUENCE 应为 5-stage（req-50 / chg-01）",
        )

    def test_new_workflow_sequence_no_ready_for_execution(self) -> None:
        from harness_workflow.workflow_helpers import WORKFLOW_SEQUENCE

        self.assertNotIn(
            "ready_for_execution",
            WORKFLOW_SEQUENCE,
            "WORKFLOW_SEQUENCE 不应含空 stage ready_for_execution（req-50 / chg-01 删除）",
        )

    def test_create_requirement_starts_at_analysis(self) -> None:
        """req-id ≥ 50 的新需求初始 stage == analysis。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            from harness_workflow.workflow_helpers import create_requirement

            create_requirement(root, "dogfood req", requirement_id="req-50")

            runtime = _get_runtime(root)
            self.assertEqual(runtime.get("stage"), "analysis",
                             "req-50 起始 stage 应为 analysis（req-50 / chg-01 D5=B）")

    def test_workflow_next_advances_analysis_to_executing(self) -> None:
        """analysis → executing 推进（need artifacts populated first for work-done gate）。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            req_flow = _create_minimal_req_state(root, "req-50", "dogfood-req", "analysis")

            # analysis 阶段 work-done gate 是 fallback=True，可以直接 next
            from harness_workflow.workflow_helpers import workflow_next
            rc = workflow_next(root)
            self.assertEqual(rc, 0, "workflow_next from analysis should succeed")

            runtime = _get_runtime(root)
            self.assertEqual(
                runtime.get("stage"), "executing",
                "analysis → executing 推进失败",
            )

    def test_workflow_full_5_stage_cycle(self) -> None:
        """5-stage 完整流转：analysis → executing → testing → acceptance → done。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            req_flow = _create_minimal_req_state(root, "req-50", "dogfood-req", "analysis")

            from harness_workflow.workflow_helpers import workflow_next

            # analysis → executing
            rc = workflow_next(root)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "executing")

            # populate executing artifacts
            _populate_executing_artifacts(req_flow)
            # executing → testing
            rc = workflow_next(root)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "testing")

            # populate testing artifacts
            _populate_testing_artifacts(req_flow)
            # testing → acceptance
            rc = workflow_next(root)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "acceptance")

            # populate acceptance artifacts
            _populate_acceptance_artifacts(req_flow)
            # acceptance → done
            rc = workflow_next(root)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "done")


# ---------------------------------------------------------------------------
# TC-02：req-id < 50 历史归档兼容旧 sequence
# ---------------------------------------------------------------------------


class TC02LegacyReqCompatTest(unittest.TestCase):
    """TC-02：req-id < 50 不走新 5-stage；D5=B 保障。"""

    def test_use_new_workflow_sequence_false_for_legacy(self) -> None:
        from harness_workflow.workflow_helpers import _use_new_workflow_sequence

        self.assertFalse(_use_new_workflow_sequence("req-49"))
        self.assertFalse(_use_new_workflow_sequence("req-01"))
        self.assertFalse(_use_new_workflow_sequence("req-1"))

    def test_create_requirement_req49_starts_at_requirement_review(self) -> None:
        """req-49（< 50）起始 stage 应为 requirement_review（legacy）。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            from harness_workflow.workflow_helpers import create_requirement

            create_requirement(root, "legacy req", requirement_id="req-49")

            runtime = _get_runtime(root)
            self.assertEqual(
                runtime.get("stage"),
                "requirement_review",
                "req-49（< 50）起始 stage 应为 requirement_review（D5=B 兼容）",
            )


# ---------------------------------------------------------------------------
# TC-03：harness next 单入口 — analysis stage_pending_user_action
# ---------------------------------------------------------------------------


class TC03HarnessNextSingleEntryTest(unittest.TestCase):
    """TC-03：harness next 单入口验证。

    analysis 阶段设置 stage_pending_user_action=confirm-execution 时，
    workflow_next 被阻断；清除 pending 后再 next 推进到 executing。
    """

    def test_next_blocked_by_pending_user_action(self) -> None:
        """stage_pending_user_action 非空时 workflow_next 返回 3（阻断）。"""
        import yaml  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            _create_minimal_req_state(root, "req-50", "next-entry-test", "analysis")

            # 注入 pending gate
            rt_path = root / ".workflow" / "state" / "runtime.yaml"
            rt = yaml.safe_load(rt_path.read_text(encoding="utf-8")) or {}
            rt["stage_pending_user_action"] = {
                "type": "confirm-execution",
                "details": {"message": "请确认执行"},
            }
            from harness_workflow.workflow_helpers import save_simple_yaml
            save_simple_yaml(rt_path, rt)

            from harness_workflow.workflow_helpers import workflow_next

            rc = workflow_next(root)
            self.assertEqual(rc, 3, "stage_pending_user_action 非空时应返回 3（阻断）")

    def test_next_advances_after_pending_cleared(self) -> None:
        """pending 清除后 workflow_next 正常推进到 executing。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            _create_minimal_req_state(root, "req-50", "next-entry-test-clear", "analysis")

            # 无 pending gate → 直接推进
            from harness_workflow.workflow_helpers import workflow_next

            rc = workflow_next(root)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "executing")

    def test_no_execute_flag_needed(self) -> None:
        """workflow_next 默认（execute=False）即可从 analysis 推进到 executing。"""
        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            _create_minimal_req_state(root, "req-50", "no-execute-flag-test", "analysis")

            from harness_workflow.workflow_helpers import workflow_next

            # execute=False（默认单入口，req-50/chg-01 废止 --execute flag）
            rc = workflow_next(root, execute=False)
            self.assertEqual(rc, 0)
            self.assertEqual(_get_runtime(root).get("stage"), "executing",
                             "harness next 单入口（execute=False）应推进到 executing")


# ---------------------------------------------------------------------------
# TC-04：done 阶段不产 sug 入池
# ---------------------------------------------------------------------------


class TC04DoneNoSugPoolTest(unittest.TestCase):
    """TC-04：done 阶段不主动入池（chg-02 落地验证）。

    验证：
    1. done.md 不含「自动提取改进建议入池」SOP
    2. extract_suggestions_from_done_report 在无 done-report.md 时返回空列表
    3. workflow_next 推进到 done 后 suggestions/ 无新文件
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = _make_harness_workspace(Path(self._tmp.name))

    def test_done_md_no_auto_extract_sop(self) -> None:
        """done.md 不含「自动提取改进建议」相关段落（chg-02 删除）。"""
        done_md = REPO_ROOT / ".workflow" / "context" / "roles" / "done.md"
        if not done_md.exists():
            self.skipTest("done.md not found")
        content = done_md.read_text(encoding="utf-8")
        # chg-02 已删除「自动提取改进建议入池」相关内容
        self.assertNotIn(
            "自动提取改进建议",
            content,
            "done.md 不应含「自动提取改进建议」（req-50 / chg-02 删除）",
        )
        self.assertNotIn(
            "自动创建 suggest 文件",
            content,
            "done.md 不应含「自动创建 suggest 文件」（req-50 / chg-02 删除）",
        )

    def test_extract_suggestions_no_done_report_returns_empty(self) -> None:
        """无 done-report.md 时 extract_suggestions_from_done_report 返回空列表。"""
        from harness_workflow.workflow_helpers import extract_suggestions_from_done_report

        result = extract_suggestions_from_done_report(self.root, "req-50")
        self.assertEqual(result, [], "无 done-report.md 应返回空列表")

    def test_workflow_next_to_done_no_new_suggestions(self) -> None:
        """推进到 done 后 suggestions/ 下无新 sug 文件（chg-02 落地）。"""
        req_flow = _create_minimal_req_state(
            self.root, "req-50", "no-sug-test", "acceptance"
        )
        _populate_acceptance_artifacts(req_flow)

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        files_before = set(sug_dir.glob("*.md"))

        from harness_workflow.workflow_helpers import workflow_next

        rc = workflow_next(self.root)
        self.assertEqual(rc, 0)
        self.assertEqual(_get_runtime(self.root).get("stage"), "done")

        files_after = set(sug_dir.glob("*.md"))
        new_sug_files = files_after - files_before
        self.assertEqual(
            len(new_sug_files),
            0,
            f"done 阶段不应产生新 sug 文件（chg-02 落地）；found: {new_sug_files}",
        )


# ---------------------------------------------------------------------------
# TC-05：渲染机器型模板正常（chg-03 + chg-04）
# ---------------------------------------------------------------------------


class TC05TemplateRenderTest(unittest.TestCase):
    """TC-05：5 个核心机器型模板 + 7 个验证交付模板渲染正常。"""

    CORE_TEMPLATES = [
        "requirement.md.tmpl",
        "change.md.tmpl",
        "change-plan.md.tmpl",
        "session-memory.md.tmpl",
        "bugfix.md.tmpl",
    ]

    DELIVERY_TEMPLATES = [
        "diagnosis.md.tmpl",
        "regression-decision.md.tmpl",
        "regression-required-inputs.md.tmpl",
        "regression-analysis.md.tmpl",
        "regression.md.tmpl",
        "test-cases.md.tmpl",
        "test-plan.md.tmpl",
    ]

    def test_core_templates_renderable(self) -> None:
        """5 个核心机器型模板可渲染（无 KeyError / render 报错）。"""
        from harness_workflow.workflow_helpers import render_template

        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            for tmpl_name in self.CORE_TEMPLATES:
                with self.subTest(template=tmpl_name):
                    try:
                        text = render_template(tmpl_name, str(root), "cn")
                        self.assertIsInstance(text, str)
                        self.assertGreater(len(text), 0, f"{tmpl_name} 渲染结果为空")
                    except Exception as exc:
                        self.fail(f"{tmpl_name} 渲染失败: {exc}")

    def test_delivery_templates_renderable(self) -> None:
        """7 个验证交付模板可渲染（无 KeyError / render 报错）。"""
        from harness_workflow.workflow_helpers import render_template

        with tempfile.TemporaryDirectory() as td:
            root = _make_harness_workspace(Path(td))
            for tmpl_name in self.DELIVERY_TEMPLATES:
                with self.subTest(template=tmpl_name):
                    try:
                        text = render_template(tmpl_name, str(root), "cn")
                        self.assertIsInstance(text, str)
                        self.assertGreater(len(text), 0, f"{tmpl_name} 渲染结果为空")
                    except Exception as exc:
                        self.fail(f"{tmpl_name} 渲染失败: {exc}")

    def test_core_templates_have_frontmatter(self) -> None:
        """核心机器型模板文件含 YAML frontmatter（---）。"""
        templates_dir = (
            REPO_ROOT
            / ".claude"
            / "skills"
            / "harness"
            / "assets"
            / "templates"
        )
        for tmpl_name in self.CORE_TEMPLATES:
            with self.subTest(template=tmpl_name):
                tmpl_path = templates_dir / tmpl_name
                if not tmpl_path.exists():
                    self.skipTest(f"template {tmpl_name} not found")
                content = tmpl_path.read_text(encoding="utf-8")
                self.assertTrue(
                    content.startswith("---"),
                    f"{tmpl_name} 应以 --- frontmatter 开始（chg-03 LLM-only 重写）",
                )

    def test_llm_only_lint_passes(self) -> None:
        """harness validate --contract llm-only-docs 在本仓库 exit 0。"""
        from harness_workflow.validate_contract import _lint_llm_only_docs

        violations = _lint_llm_only_docs(REPO_ROOT)
        self.assertEqual(
            violations,
            [],
            f"llm-only-docs lint 发现违规：\n" + "\n".join(violations),
        )


# ---------------------------------------------------------------------------
# TC-06：reviewer.md / review-checklist.md 含新加项
# ---------------------------------------------------------------------------


class TC06ReviewerLintItemsTest(unittest.TestCase):
    """TC-06：reviewer.md + review-checklist.md 含 req-50 / chg-05 新加 lint 项。"""

    def _read_reviewer_md(self) -> str:
        p = REPO_ROOT / ".workflow" / "context" / "roles" / "reviewer.md"
        self.assertTrue(p.exists(), f"reviewer.md not found at {p}")
        return p.read_text(encoding="utf-8")

    def _read_review_checklist_md(self) -> str:
        p = REPO_ROOT / ".workflow" / "context" / "checklists" / "review-checklist.md"
        self.assertTrue(p.exists(), f"review-checklist.md not found at {p}")
        return p.read_text(encoding="utf-8")

    def test_reviewer_md_has_llm_only_lint_section(self) -> None:
        content = self._read_reviewer_md()
        self.assertIn(
            "LLM-only 文档 lint",
            content,
            "reviewer.md 应含「LLM-only 文档 lint」段（req-50 / chg-05）",
        )

    def test_reviewer_md_has_stage_self_check_section(self) -> None:
        content = self._read_reviewer_md()
        self.assertIn(
            "新加 stage 自检",
            content,
            "reviewer.md 应含「新加 stage 自检」段（req-50 / chg-05）",
        )

    def test_reviewer_md_has_done_no_sug_pool_section(self) -> None:
        content = self._read_reviewer_md()
        self.assertIn(
            "done 主动入池防回退",
            content,
            "reviewer.md 应含「done 主动入池防回退」段（req-50 / chg-02 + chg-05）",
        )

    def test_review_checklist_md_has_llm_only_lint_section(self) -> None:
        content = self._read_review_checklist_md()
        self.assertIn(
            "LLM-only 文档 lint",
            content,
            "review-checklist.md 应含「LLM-only 文档 lint」段（req-50 / chg-05）",
        )

    def test_review_checklist_md_has_stage_self_check_section(self) -> None:
        content = self._read_review_checklist_md()
        self.assertIn(
            "新加 stage 自检",
            content,
            "review-checklist.md 应含「新加 stage 自检」段（req-50 / chg-05）",
        )

    def test_review_checklist_md_has_done_no_sug_pool_section(self) -> None:
        content = self._read_review_checklist_md()
        self.assertIn(
            "done 主动入池防回退",
            content,
            "review-checklist.md 应含「done 主动入池防回退」段（req-50 / chg-02 + chg-05）",
        )

    def test_review_checklist_md_has_new_contract_fix_checklist_item(self) -> None:
        """review-checklist.md 含新加 contract 配套 fix-checklist 项（继承 req-48 经验）。"""
        content = self._read_review_checklist_md()
        self.assertIn(
            "新加 contract 配套 fix-checklist",
            content,
            "review-checklist.md 应含「新加 contract 配套 fix-checklist」项（req-50 / chg-05，继承 req-48 经验）",
        )

    def test_reviewer_md_scaffold_mirror_in_sync(self) -> None:
        """reviewer.md live == scaffold_v2 mirror（硬门禁五）。"""
        live = REPO_ROOT / ".workflow" / "context" / "roles" / "reviewer.md"
        mirror = (
            REPO_ROOT
            / "src"
            / "harness_workflow"
            / "assets"
            / "scaffold_v2"
            / ".workflow"
            / "context"
            / "roles"
            / "reviewer.md"
        )
        self.assertTrue(live.exists())
        self.assertTrue(mirror.exists(), f"scaffold mirror 未同步: {mirror}")
        self.assertEqual(
            live.read_bytes(),
            mirror.read_bytes(),
            "reviewer.md live 与 scaffold_v2 mirror 字节不一致（硬门禁五）",
        )

    def test_review_checklist_md_scaffold_mirror_in_sync(self) -> None:
        """review-checklist.md live == scaffold_v2 mirror（硬门禁五）。"""
        live = REPO_ROOT / ".workflow" / "context" / "checklists" / "review-checklist.md"
        mirror = (
            REPO_ROOT
            / "src"
            / "harness_workflow"
            / "assets"
            / "scaffold_v2"
            / ".workflow"
            / "context"
            / "checklists"
            / "review-checklist.md"
        )
        self.assertTrue(live.exists())
        self.assertTrue(mirror.exists(), f"scaffold mirror 未同步: {mirror}")
        self.assertEqual(
            live.read_bytes(),
            mirror.read_bytes(),
            "review-checklist.md live 与 scaffold_v2 mirror 字节不一致（硬门禁五）",
        )


if __name__ == "__main__":
    unittest.main()
