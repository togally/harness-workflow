r"""End-to-end smoke for req-28 / chg-07（覆盖 AC-11 + AC-07 + 联动 AC-09/10/12/13/14/15）。

本 smoke 在 **tempdir 隔离** 环境里串起以下 7 条 AC 的集成断言（参考 req-26 chg-06
smoke 的组合风格）：

1. ``test_full_lifecycle_with_bugfix_and_archive``：
   - req 全链路（requirement_review → done）→ archive；
   - bugfix 分支（BUGFIX_SEQUENCE：regression → executing → testing → acceptance → done）
     → ``archive --force-done``；
   - 断言 bugfix runtime 写 ``operation_type="bugfix"``、state yaml stage 同步、
     archive 路径无双层 branch、``active_requirements`` 清理干净。
     （AC-12 + AC-03 扩展 + AC-14 + AC-05）

2. ``test_suggest_cli_handles_no_frontmatter``：无 frontmatter 也能 delete / apply。
   （AC-15）

3. ``test_suggest_numbering_monotonic_across_archive``：当前空 + archive 含历史
   sug-NN 时，新建 sug 编号必须单调递增（跨 archive 聚合）。（AC-15）

4. ``test_cycle_detector_import_and_basic_detect``：``from harness_workflow import ...``
   六符号导出齐全；构造 3 节点链带重复 role → ``detect_subagent_cycle`` 返回
   ``has_cycle=True``。（AC-13）

5. ``test_validate_human_docs_reports_missing_and_present``：构造部分齐的 artifacts
   → ``validate_human_docs`` 正确区分 ``[✓]`` / ``[ ]``。（AC-09）

6. ``test_readme_has_refresh_template_hint``：本仓库 README.md / README.zh.md
   均含 ``pip install -U harness-workflow`` 字样（下游刷新模板提示）。（AC-10）

硬约束（briefing 一致）：
- 不跑真 ``harness`` CLI 命令；
- 不碰 chg-01~06 已完成的代码；
- 不污染本仓库 ``.workflow/state/`` 与 ``artifacts/``；
- 每条用例独立可读。
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


# ---------------------------------------------------------------------------
# Helpers：铺最小工作区（与 test_smoke_req26 对齐）
# ---------------------------------------------------------------------------


def _make_harness_workspace(tmpdir: Path, language: str = "english") -> Path:
    """构造最小可用的 harness workspace（与既有 test_*_helpers.py 对齐）。"""
    root = tmpdir / "repo"
    (root / ".workflow" / "context").mkdir(parents=True)
    (root / ".workflow" / "state").mkdir(parents=True)
    (root / ".workflow" / "state" / "requirements").mkdir(parents=True)
    (root / ".workflow" / "state" / "bugfixes").mkdir(parents=True)
    (root / ".workflow" / "state" / "sessions").mkdir(parents=True)
    (root / ".workflow" / "flow" / "suggestions").mkdir(parents=True)
    (root / "artifacts" / "main" / "requirements").mkdir(parents=True)
    (root / "artifacts" / "main" / "bugfixes").mkdir(parents=True)
    (root / ".codex" / "harness").mkdir(parents=True)
    (root / ".codex" / "harness" / "config.json").write_text(
        json.dumps({"language": language}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
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


# ---------------------------------------------------------------------------
# 1) 全生命周期 smoke：req + bugfix + archive（AC-11 + AC-12 + AC-14 + AC-05）
# ---------------------------------------------------------------------------


class FullLifecycleSmokeTest(unittest.TestCase):
    """端到端 smoke：一个 tempdir 里顺跑 req 全链路 → archive，再顺跑 bugfix → archive --force-done。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-smoke-req28-full-"))
        self.root = _make_harness_workspace(self.tempdir, language="english")
        self._branch_patch = mock.patch(
            "harness_workflow.workflow_helpers._get_git_branch",
            return_value="main",
        )
        self._branch_patch.start()
        # archive 入口可能交互询问 commit，mock input 直接回 "n"
        self._input_patch = mock.patch("builtins.input", return_value="n")
        self._input_patch.start()

    def tearDown(self) -> None:
        self._input_patch.stop()
        self._branch_patch.stop()
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_full_lifecycle_with_bugfix_and_archive(self) -> None:
        from harness_workflow.workflow_helpers import (
            archive_requirement,
            create_bugfix,
            create_change,
            create_requirement,
            load_requirement_runtime,
            load_simple_yaml,
            workflow_next,
        )

        # --- 阶段 A：req 全链路 requirement_review → done → archive ----------
        rc = create_requirement(self.root, "demo-req")
        self.assertEqual(rc, 0)

        runtime = load_requirement_runtime(self.root)
        req_id = str(runtime["current_requirement"])
        self.assertRegex(req_id, r"^req-\d+$")
        self.assertEqual(str(runtime["stage"]), "requirement_review")

        reqs_base = self.root / "artifacts" / "main" / "requirements"
        req_dirs = [d for d in reqs_base.iterdir() if d.is_dir()]
        self.assertEqual(len(req_dirs), 1)
        req_dir = req_dirs[0]
        state_path = self.root / ".workflow" / "state" / "requirements" / f"{req_dir.name}.yaml"

        # requirement_review → planning（P-1 default-pick C, req-31 chg-01）
        self.assertEqual(workflow_next(self.root, execute=False), 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "planning")

        # 造一个 change，才能继续 ready_for_execution
        self.assertEqual(create_change(self.root, "demo-chg"), 0)

        # planning → ready_for_execution → executing（合并后序列，移除 plan_review）
        self.assertEqual(workflow_next(self.root, execute=False), 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "ready_for_execution")
        self.assertEqual(workflow_next(self.root, execute=True), 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "executing")

        # executing → testing → acceptance → done
        self.assertEqual(workflow_next(self.root, execute=False), 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "testing")
        self.assertEqual(workflow_next(self.root, execute=False), 0)
        self.assertEqual(load_simple_yaml(state_path).get("stage"), "acceptance")
        self.assertEqual(workflow_next(self.root, execute=False), 0)
        state_done = load_simple_yaml(state_path)
        self.assertEqual(state_done.get("stage"), "done")
        self.assertEqual(state_done.get("status"), "done",
                         "推到 done 时 status 应自动写回为 done（AC-03）")

        # archive req → artifacts/main/archive/requirements/<dir>（AC-05 单层 branch）
        self.assertEqual(archive_requirement(self.root, req_dir.name), 0)
        archive_root = self.root / "artifacts" / "main" / "archive"
        archived_req = archive_root / "requirements" / req_dir.name
        self.assertTrue(archived_req.exists(), "req 归档应落到 archive/requirements/")
        self.assertFalse(
            (archive_root / "main").exists(),
            "AC-05：archive 下不应出现 main/ 子目录（双层 branch）",
        )

        # active_requirements 已清理 req（AC-14 的 requirement 分支同样行为）
        runtime_after_req = load_requirement_runtime(self.root)
        self.assertNotIn(req_id, runtime_after_req.get("active_requirements", []))

        # --- 阶段 B：bugfix 分支 BUGFIX_SEQUENCE → done → archive --force-done ---
        self.assertEqual(create_bugfix(self.root, "demo-bugfix"), 0)
        runtime_bf = load_requirement_runtime(self.root)
        bugfix_id = str(runtime_bf.get("operation_target", "")).strip()
        self.assertTrue(bugfix_id.startswith("bugfix-"), f"operation_target 应以 bugfix- 开头：{bugfix_id!r}")
        # AC-12：bugfix 写入 operation_type + current_requirement + stage=regression
        self.assertEqual(runtime_bf.get("operation_type"), "bugfix")
        self.assertEqual(runtime_bf.get("current_requirement"), bugfix_id)
        self.assertEqual(runtime_bf.get("stage"), "regression")

        # 找到 bugfix state yaml
        bugfix_state_dir = self.root / ".workflow" / "state" / "bugfixes"
        bugfix_yamls = [
            p for p in bugfix_state_dir.iterdir()
            if p.is_file() and p.suffix == ".yaml" and (p.stem == bugfix_id or p.stem.startswith(bugfix_id + "-"))
        ]
        self.assertEqual(len(bugfix_yamls), 1, f"应正好一个 bugfix state yaml，实际 {bugfix_yamls}")
        bugfix_state_path = bugfix_yamls[0]

        # 走完 BUGFIX_SEQUENCE: regression → executing → testing → acceptance → done
        for expected in ["executing", "testing", "acceptance", "done"]:
            self.assertEqual(workflow_next(self.root, execute=False), 0)
            state = load_simple_yaml(bugfix_state_path)
            self.assertEqual(
                state.get("stage"), expected,
                f"bugfix state yaml stage 应同步到 {expected}，实际 {state!r}",
            )
            # AC-12：推进后 operation_type / operation_target 必须保留
            rt = load_requirement_runtime(self.root)
            self.assertEqual(rt.get("operation_type"), "bugfix",
                             f"推进到 {expected} 后 operation_type 必须保留")
            self.assertEqual(rt.get("operation_target"), bugfix_id)
            self.assertEqual(rt.get("stage"), expected)

        # bugfix 目录名
        bugfix_artifact_dirs = [
            d for d in (self.root / "artifacts" / "main" / "bugfixes").iterdir() if d.is_dir()
        ]
        self.assertEqual(len(bugfix_artifact_dirs), 1)
        bugfix_dir_name = bugfix_artifact_dirs[0].name

        # archive bugfix（已 done，force_done 实际是 no-op，但调用方强约束写 force_done）
        self.assertEqual(archive_requirement(self.root, bugfix_id, force_done=True), 0)

        archived_bf = archive_root / "bugfixes" / bugfix_dir_name
        self.assertTrue(
            archived_bf.exists(),
            f"bugfix 归档应落到 archive/bugfixes/{bugfix_dir_name}",
        )
        # AC-14：archive/bugfixes/ 下保留 state.yaml
        self.assertTrue((archived_bf / "state.yaml").exists(),
                        "归档目录内应含 state.yaml（AC-14）")
        # AC-05：依旧不得出现双层 branch
        self.assertFalse((archive_root / "main").exists())

        # AC-14：active_requirements 清理 bugfix_id
        runtime_final = load_requirement_runtime(self.root)
        active_ids = [str(x) for x in runtime_final.get("active_requirements", [])]
        self.assertNotIn(
            bugfix_id, active_ids,
            f"归档后 active_requirements 不应再含 {bugfix_id}，实际 {active_ids}",
        )


# ---------------------------------------------------------------------------
# 2 / 3) suggest CLI 无 frontmatter + 编号单调（AC-15）
# ---------------------------------------------------------------------------


class SuggestCliSmokeTest(unittest.TestCase):
    """AC-15：filename fallback + 跨 archive 单调递增。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-smoke-req28-sug-"))
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

    def test_suggest_cli_handles_no_frontmatter(self) -> None:
        """(a) 无 frontmatter 的 sug 可被 delete；(b) 带 frontmatter 的 sug 可被 apply。"""
        from harness_workflow.workflow_helpers import (
            apply_suggestion,
            delete_suggestion,
        )

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"

        # (a) 无 frontmatter 的 sug → delete 成功
        no_fm_path = sug_dir / "sug-50-no-frontmatter.md"
        no_fm_path.write_text(
            "# 一条没有 frontmatter 的历史建议\n\n正文内容。\n", encoding="utf-8"
        )
        self.assertEqual(delete_suggestion(self.root, "sug-50"), 0)
        self.assertFalse(no_fm_path.exists(), "sug-50 应被删除（filename fallback 生效）")

        # (b) 带 frontmatter 的 sug → apply 成功
        fm_path = sug_dir / "sug-60-apply-demo.md"
        fm_path.write_text(
            "---\nid: sug-60\ntitle: apply demo\nstatus: pending\ncreated_at: 2026-04-19\npriority: medium\n---\n\n"
            "用 apply 验证 frontmatter 正常路径。\n",
            encoding="utf-8",
        )
        with mock.patch(
            "harness_workflow.workflow_helpers.create_requirement",
            return_value=0,
        ) as create_mock:
            rc = apply_suggestion(self.root, "sug-60")
        self.assertEqual(rc, 0)
        self.assertTrue(create_mock.called)
        # bugfix-3：apply 成功后源 sug 被 move 到 archive/（sug-06 归档惯例对齐）。
        self.assertFalse(fm_path.exists(), "apply 成功后源路径不应再存在")
        archived = sug_dir / "archive" / "sug-60-apply-demo.md"
        self.assertTrue(archived.exists(), "apply 成功后 sug 应被搬到 archive/")
        text = archived.read_text(encoding="utf-8")
        self.assertIn("status: applied", text, "apply 应把 status: pending → applied")

    def test_suggest_numbering_monotonic_across_archive(self) -> None:
        """当前目录为空 + archive 含 sug-80 → 新建必须为 sug-81（跨 archive 单调递增）。"""
        from harness_workflow.workflow_helpers import create_suggestion

        sug_dir = self.root / ".workflow" / "flow" / "suggestions"
        archive_dir = sug_dir / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        (archive_dir / "sug-80-historical.md").write_text(
            "---\nid: sug-80\nstatus: archived\n---\n\n归档正文。\n", encoding="utf-8"
        )

        # 前置：当前目录无 sug-*.md
        self.assertEqual(
            len(list(sug_dir.glob("sug-*.md"))), 0,
            "前置：suggestions/ 当前目录应为空",
        )

        # req-31 / chg-01 Step 1.2：create_suggestion 现在要求 title 必填（契约 6）。
        self.assertEqual(
            create_suggestion(
                self.root,
                "跨 archive 单调递增样例",
                title="跨 archive 单调递增样例",
            ),
            0,
        )

        new_files = sorted(sug_dir.glob("sug-*.md"))
        self.assertEqual(len(new_files), 1)
        name = new_files[0].name
        self.assertTrue(
            name.startswith("sug-81-"),
            f"新建 sug 应以 sug-81- 开头（跨 archive 递增），实际 {name}",
        )


# ---------------------------------------------------------------------------
# 4) cycle-detection import + 基础检测（AC-13）
# ---------------------------------------------------------------------------


class CycleDetectorSmokeTest(unittest.TestCase):
    """AC-13：harness_workflow 顶层导出 cycle-detection API，基本语义正确。"""

    def test_cycle_detector_import_and_basic_detect(self) -> None:
        # (a) 顶层 re-export 7 符号齐全；逐个 import 不得抛
        from harness_workflow import (  # noqa: F401
            CallChainNode,
            CycleDetectionResult,
            CycleDetector,
            detect_subagent_cycle,
            get_cycle_detector,
            report_cycle_detection,
            reset_cycle_detector,
        )

        # (b) 构造 3 节点链（A → B → C）+ 新节点复用 A 的 agent_id → cycle
        a = CallChainNode(level=0, agent_id="agent-A", role="director", task="", session_memory_path="")
        b = CallChainNode(
            level=1, agent_id="agent-B", role="executing", task="",
            session_memory_path="", parent_agent_id="agent-A",
        )
        c = CallChainNode(
            level=2, agent_id="agent-C", role="executing", task="",
            session_memory_path="", parent_agent_id="agent-B",
        )
        chain = [a, b, c]

        # 新节点 agent_id == A → 必须命中 cycle
        result = detect_subagent_cycle(chain, new_agent_id="agent-A", new_role="director")
        self.assertTrue(result.has_cycle, f"expected cycle, got {result!r}")
        self.assertIn("agent-A", result.cycle_path)
        self.assertIn("Cycle detected", result.message)

        # (c) 反例：新节点 agent_id 全新 → 无 cycle
        result_ok = detect_subagent_cycle(chain, new_agent_id="agent-D")
        self.assertFalse(result_ok.has_cycle)

        # (d) CycleDetector 单例 push/pop/重置语义
        reset_cycle_detector()
        det = get_cycle_detector()
        self.assertIs(det, get_cycle_detector(), "get_cycle_detector 应为单例")
        r1 = det.add_node(a)
        self.assertFalse(r1.has_cycle)
        r2 = det.add_node(b)
        self.assertFalse(r2.has_cycle)
        r3 = det.add_node(
            CallChainNode(level=2, agent_id="agent-A", role="director", task="", session_memory_path="")
        )
        self.assertTrue(r3.has_cycle, "第 3 个节点复用 agent-A 应命中 cycle")
        # 命中 cycle 的节点不会被压入链
        self.assertEqual(det.get_chain_depth(), 2)
        reset_cycle_detector()
        self.assertIsNot(det, get_cycle_detector(), "reset 后应返回新实例")


# ---------------------------------------------------------------------------
# 5) validate_human_docs 部分齐 → 区分 ok / missing（AC-09）
# ---------------------------------------------------------------------------


class ValidateHumanDocsSmokeTest(unittest.TestCase):
    """AC-09：对人文档校验能正确区分 [✓] / [ ]。"""

    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="harness-smoke-req28-vhd-"))
        self.root = self.tempdir / "repo"
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def test_validate_human_docs_reports_missing_and_present(self) -> None:
        """AC-09：对人文档校验能正确区分 [✓] / [ ]。

        req-40（39 <= req-id <= 40，现行扫描，含四类 brief）走新规扁平路径：
        - req 级：需求摘要.md / 交付总结.md（废止项 testing/acceptance 已从常量删除）
        - chg 级：req 根目录 chg-NN- 前缀文件（不再依赖 changes/ 子目录）

        注：原测试用 req-77，但 req-77 >= BRIEF_DEPRECATED_FROM_REQ_ID(41) 走精简扫描；
        改用 req-40（现行扫描仍含四类 brief）验证 [✓]/[ ] 区分行为。
        更新溯源：req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-02
        （validate_human_docs 重写 + 精简废止项）/ req-41（废四类 brief）/ chg-03（重写删四类 brief）。
        """
        from harness_workflow.validate_human_docs import (
            CHANGE_LEVEL_DOCS,
            REQ_LEVEL_DOCS,
            STATUS_MISSING,
            STATUS_OK,
            format_report,
            validate_human_docs,
        )

        # 构造 req-40-demo（现行扫描，含四类 brief）：
        # 写 需求摘要.md + chg-01-变更简报.md，缺 交付总结.md + chg-01-实施说明.md
        req_dir = self.root / "artifacts" / "main" / "requirements" / "req-40-demo"
        req_dir.mkdir(parents=True)
        (req_dir / "需求摘要.md").write_text("stub", encoding="utf-8")
        (req_dir / "chg-01-变更简报.md").write_text("stub", encoding="utf-8")
        # 故意不写 交付总结.md / chg-01-实施说明.md → missing

        kind, target_id, items = validate_human_docs(self.root, "req-40")
        self.assertEqual(kind, "req")
        self.assertEqual(target_id, "req-40-demo")
        # 现行扫描：2 req-level（需求摘要 + 交付总结）+ 2 chg-level（变更简报 + 实施说明）= 4
        self.assertEqual(
            len(items),
            len(REQ_LEVEL_DOCS) + len(CHANGE_LEVEL_DOCS),
            f"items 数应为 req-level({len(REQ_LEVEL_DOCS)}) + change-level({len(CHANGE_LEVEL_DOCS)})，实际 {items!r}",
        )

        by_name = {i.filename: i for i in items}
        self.assertEqual(by_name["需求摘要.md"].status, STATUS_OK)
        self.assertEqual(by_name["交付总结.md"].status, STATUS_MISSING)
        self.assertEqual(by_name["chg-01-变更简报.md"].status, STATUS_OK)
        self.assertEqual(by_name["chg-01-实施说明.md"].status, STATUS_MISSING)
        # 废止项不再出现在 items 中
        self.assertNotIn("测试结论.md", by_name)
        self.assertNotIn("验收摘要.md", by_name)

        # format_report 含 [✓] / [ ] 两种 icon
        text = format_report(kind, target_id, items)
        self.assertIn("[✓]", text)
        self.assertIn("[ ]", text)
        self.assertIn("req-40-demo", text)


# ---------------------------------------------------------------------------
# 6) README 下游刷新模板提示（AC-10）
# ---------------------------------------------------------------------------


class ReadmeRefreshHintTest(unittest.TestCase):
    """AC-10：README.md / README.zh.md 含 pip install -U harness-workflow 提示。"""

    def test_readme_has_refresh_template_hint(self) -> None:
        readme_en = REPO_ROOT / "README.md"
        readme_zh = REPO_ROOT / "README.zh.md"
        # 至少有一个 README 存在（防止后续改名），两个都存在时都要包含提示
        self.assertTrue(readme_en.exists() or readme_zh.exists(), "README 必须存在")

        hint = "pip install -U harness-workflow"
        if readme_en.exists():
            self.assertIn(
                hint, readme_en.read_text(encoding="utf-8"),
                f"{readme_en.name} 必须含 `{hint}` 下游刷新模板提示（AC-10）",
            )
        if readme_zh.exists():
            self.assertIn(
                hint, readme_zh.read_text(encoding="utf-8"),
                f"{readme_zh.name} 必须含 `{hint}` 下游刷新模板提示（AC-10）",
            )


if __name__ == "__main__":
    unittest.main()
