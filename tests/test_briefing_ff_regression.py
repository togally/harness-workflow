"""req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO
派发 briefing 注入 task_context_index + 快照落盘）扩展：ff --auto / regression 派发路径。

覆盖 AC-03 的全量范围：让 `harness ff --auto` 和 `harness regression` 两条派发路径也
产出 subagent briefing（当前只有 `harness next --execute` 产）。

测试清单：
1. ff --auto 一次性推进到最终落点后，stdout 含 briefing fence + 非空 task_context_index
2. ff --auto 落到终局 stage（done / archive）时**不**打 briefing
3. regression 创建新 regression 时，stdout 含 briefing，内含 regression_id / regression_title 字段
4. regression --confirm 后**不**重复派发 briefing（confirm 只确认真实性，状态保持）
5. `_build_subagent_briefing` 既有调用签名（不传 regression_id）仍工作，字段不出现在 JSON 中（向后兼容断言）
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_briefing_json(text: str) -> dict | None:
    """从 subagent briefing fence 中抽取 JSON 并 loads；未找到返回 None。"""
    match = re.search(r"```subagent-briefing\n(\{.*?\})\n```", text, flags=re.DOTALL)
    if match is None:
        return None
    return json.loads(match.group(1))


def _touch(p: Path, text: str = "") -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _bootstrap_repo(
    root: Path,
    req_id: str,
    *,
    stage: str = "requirement_review",
    operation_type: str = "requirement",
    current_regression: str = "",
    current_regression_title: str = "",
) -> None:
    """构造最小可用的 harness repo：runtime.yaml + state yaml + 默认 role 文件 + artifacts 目录。"""
    from harness_workflow.workflow_helpers import save_requirement_runtime

    # 默认 role/stage/base 文件（task_context_index 能命中几条）
    _touch(root / ".workflow/context/roles/requirement-review.md")
    _touch(root / ".workflow/context/roles/planning.md")
    _touch(root / ".workflow/context/roles/executing.md")
    _touch(root / ".workflow/context/roles/testing.md")
    _touch(root / ".workflow/context/roles/acceptance.md")
    _touch(root / ".workflow/context/roles/regression.md")
    _touch(root / ".workflow/context/roles/stage-role.md")
    _touch(root / ".workflow/context/roles/base-role.md")

    runtime = {
        "operation_type": operation_type,
        "operation_target": req_id,
        "current_requirement": req_id,
        "current_requirement_title": "演示需求",
        "stage": stage,
        "stage_entered_at": "2026-04-21T00:00:00+00:00",
        "conversation_mode": "open",
        "locked_requirement": "",
        "locked_stage": "",
        "current_regression": current_regression,
        "current_regression_title": current_regression_title,
        "ff_mode": False,
        "ff_stage_history": [],
        "active_requirements": [req_id],
    }
    save_requirement_runtime(root, runtime)

    # state/requirements/{req_id}.yaml（_sync_stage_to_state_yaml 需要）
    state_dir = root / ".workflow" / "state" / "requirements"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{req_id}.yaml").write_text(
        f"id: {req_id}\ntitle: 演示需求\nstage: {stage}\nstatus: active\n",
        encoding="utf-8",
    )

    # artifacts/{branch}/requirements/{req_id}-demo（write_decision_summary / create_regression 寻址）
    artifacts_dir = root / "artifacts" / "main" / "requirements" / f"{req_id}-演示需求"
    artifacts_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 测试 1：ff --auto 最终落点派发 briefing
# ---------------------------------------------------------------------------
class FfAutoBriefingTests(unittest.TestCase):
    def test_ff_auto_emits_briefing_at_final_stage(self) -> None:
        """req-32 / chg-03 扩展：ff --auto 推进到非终局 stage（testing）时 stdout 含 briefing + 非空 task_context_index。"""
        from harness_workflow.ff_auto import workflow_ff_auto

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_repo(root, "req-99", stage="requirement_review")

            # 捕获 stdout
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = workflow_ff_auto(root, auto_accept="all")
            self.assertEqual(rc, 0)

            out = buf.getvalue()
            payload = _extract_briefing_json(out)
            self.assertIsNotNone(payload, f"ff --auto 未打 briefing fence: {out!r}")
            # stage 字段应为最终落点（testing / ready_for_execution 之一，取决于 sequence）
            self.assertIn(payload["stage"], ("testing", "ready_for_execution", "executing"))
            # task_context_index 应非空（默认 role 集至少命中 3 条）
            self.assertIsInstance(payload.get("task_context_index"), list)
            self.assertGreater(len(payload["task_context_index"]), 0)
            # 每条含 path + reason
            for item in payload["task_context_index"]:
                self.assertIn("path", item)
                self.assertIn("reason", item)
            # 快照文件应落盘
            snap_rel = payload.get("task_context_index_file", "")
            self.assertTrue(snap_rel, "task_context_index_file 不应为空")
            self.assertTrue((root / snap_rel).exists(), f"快照未落盘: {snap_rel}")

    def test_ff_auto_no_briefing_at_terminal_stage(self) -> None:
        """req-32 / chg-03 扩展：ff --auto 已在 acceptance/done 原地不动时，不打 briefing（符合 _NO_BRIEFING_STAGES 契约）。

        设计理由：`_advance_to_stage_before_acceptance` 若当前 stage 已越过目标，返回 from==to，
        主入口应据此跳过 briefing，避免向已完成的 subagent 派发。
        """
        from harness_workflow.ff_auto import workflow_ff_auto

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # 直接在 done 启动：_advance_to_stage_before_acceptance 应返回 from==to
            _bootstrap_repo(root, "req-99", stage="done")

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = workflow_ff_auto(root, auto_accept="all")
            self.assertEqual(rc, 0)

            out = buf.getvalue()
            payload = _extract_briefing_json(out)
            self.assertIsNone(payload, f"ff --auto 在 done 原地不动，不应打 briefing；实际: {out!r}")


# ---------------------------------------------------------------------------
# 测试 2：regression 派发 briefing + regression_id / regression_title 字段
# ---------------------------------------------------------------------------
class RegressionBriefingTests(unittest.TestCase):
    def test_create_regression_emits_briefing_with_regression_fields(self) -> None:
        """req-32 / chg-03 扩展：create_regression 执行后，stdout 含 briefing，stage=regression 且含 regression_id / regression_title。"""
        from harness_workflow.workflow_helpers import create_regression

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_repo(root, "req-99", stage="testing")

            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = create_regression(root, "登录接口异常")
            self.assertEqual(rc, 0)

            out = buf.getvalue()
            payload = _extract_briefing_json(out)
            self.assertIsNotNone(payload, f"create_regression 未打 briefing: {out!r}")
            self.assertEqual(payload["stage"], "regression")
            self.assertEqual(payload["requirement_id"], "req-99")
            # regression_id 字段应注入（reg-NN 形式）
            self.assertIn("regression_id", payload)
            self.assertRegex(payload["regression_id"], r"^reg-\d+$")
            self.assertEqual(payload.get("regression_title", ""), "登录接口异常")
            # task_context_index 应非空（regression role 存在）
            self.assertIsInstance(payload.get("task_context_index"), list)
            self.assertGreater(len(payload["task_context_index"]), 0)

    def test_regression_confirm_no_briefing(self) -> None:
        """req-32 / chg-03 扩展：regression --confirm 只做状态标记，不重复派发 briefing。

        设计理由：--confirm 的语义是"确认问题真实"，此时 subagent（诊断师）已经完成分析；
        重复派发会误导为"再诊断一次"。confirmed 后的下一步（--testing / --change /
        --requirement）各自派发对应 stage 的 briefing（由既有 workflow_next 链路兜底）。
        """
        from harness_workflow.workflow_helpers import (
            create_regression,
            regression_action,
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_repo(root, "req-99", stage="testing")

            # 先建一个 regression（会产 briefing，吞掉）
            buf = io.StringIO()
            with redirect_stdout(buf):
                create_regression(root, "登录接口异常")

            # confirm 阶段
            buf_confirm = io.StringIO()
            with redirect_stdout(buf_confirm):
                rc = regression_action(root, confirm=True)
            self.assertEqual(rc, 0)

            out = buf_confirm.getvalue()
            payload = _extract_briefing_json(out)
            self.assertIsNone(payload, f"--confirm 不应重复派发 briefing；实际: {out!r}")


# ---------------------------------------------------------------------------
# 测试 3：_build_subagent_briefing 向后兼容（regression_id 缺省时字段不出现）
# ---------------------------------------------------------------------------
class BuildBriefingBackwardCompatTests(unittest.TestCase):
    def test_build_briefing_without_regression_id_kwarg(self) -> None:
        """req-32 / chg-03 扩展：未传 regression_id 时 JSON 不含 regression_id / regression_title 字段，保持既有测试基线。"""
        from harness_workflow.workflow_helpers import _build_subagent_briefing

        text = _build_subagent_briefing("executing", "req-99", "演示需求")
        payload = _extract_briefing_json(text)
        self.assertIsNotNone(payload)
        self.assertNotIn("regression_id", payload)
        self.assertNotIn("regression_title", payload)

    def test_build_briefing_with_regression_id_kwarg(self) -> None:
        """req-32 / chg-03 扩展：传入 regression_id/title 时 JSON 含两字段。"""
        from harness_workflow.workflow_helpers import _build_subagent_briefing

        text = _build_subagent_briefing(
            "regression",
            "req-99",
            "演示需求",
            regression_id="reg-07",
            regression_title="登录失败",
        )
        payload = _extract_briefing_json(text)
        self.assertIsNotNone(payload)
        self.assertEqual(payload["regression_id"], "reg-07")
        self.assertEqual(payload["regression_title"], "登录失败")


if __name__ == "__main__":
    unittest.main()
