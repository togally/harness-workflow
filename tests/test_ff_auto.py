"""req-29 / chg-04：`harness ff --auto` CLI 入口与三档 ack 的单元测试。

覆盖：
- ``workflow_ff_auto`` 推进 stage 到 ``acceptance`` 前一步停下（非 acceptance / done）；
- ``--auto-accept low`` 仅对 low 风险决策点自动 ack，其它交互；
- ``--auto-accept all`` 全部自动 ack（但阻塞类别仍强制交互）；
- 未传 ``--auto-accept`` 时每条决策点都交互；
- 进入 acceptance 前 ``决策汇总.md`` 已落盘。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from harness_workflow.decision_log import (  # noqa: E402
    DecisionPoint,
    append_decision,
)
from harness_workflow.ff_auto import (  # noqa: E402
    _should_auto_ack,
    check_blocking_before_action,
    workflow_ff_auto,
)
from harness_workflow.workflow_helpers import (  # noqa: E402
    load_requirement_runtime,
    save_requirement_runtime,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def _bootstrap_requirement_repo(root: Path, req_id: str, stage: str = "requirement_review") -> None:
    """在临时仓库里写一份最小可用的 runtime.yaml + artifacts 目录骨架。

    让 ``workflow_ff_auto`` 能 load runtime / write summary，不依赖真实 git。
    """
    runtime_path = root / ".workflow" / "state" / "runtime.yaml"
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime = {
        "operation_type": "requirement",
        "operation_target": req_id,
        "current_requirement": req_id,
        "stage": stage,
        "stage_entered_at": "2026-04-19T00:00:00+00:00",
        "conversation_mode": "open",
        "locked_requirement": "",
        "locked_stage": "",
        "current_regression": "",
        "ff_mode": False,
        "ff_stage_history": [],
        "active_requirements": [req_id],
    }
    save_requirement_runtime(root, runtime)

    # state/requirements/{req_id}.yaml（_sync_stage_to_state_yaml 需要）。
    state_dir = root / ".workflow" / "state" / "requirements"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / f"{req_id}.yaml").write_text(
        f"id: {req_id}\ntitle: demo\nstage: {stage}\nstatus: active\n",
        encoding="utf-8",
    )

    # artifacts/{branch}/requirements/{req_id}-demo/（write_decision_summary 寻址）。
    artifacts_dir = root / "artifacts" / "main" / "requirements" / f"{req_id}-demo"
    artifacts_dir.mkdir(parents=True, exist_ok=True)


def _dp(
    *,
    id_: str,
    risk: str = "low",
    description: str = "普通决策",
    options: list[str] | None = None,
    choice: str = "A",
) -> DecisionPoint:
    return DecisionPoint(
        id=id_,
        timestamp="2026-04-19T10:00:00Z",
        stage="planning",
        risk=risk,
        description=description,
        options=list(options or ["A", "B"]),
        choice=choice,
        reason="测试理由",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class FfAutoStageAdvanceTests(unittest.TestCase):
    def test_ff_auto_stops_before_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_requirement_repo(root, "req-99", stage="requirement_review")

            rc = workflow_ff_auto(root, auto_accept="all", output_writer=lambda m: None)
            self.assertEqual(rc, 0)

            runtime = load_requirement_runtime(root)
            final_stage = str(runtime.get("stage", "")).strip()
            # 只要不等于 acceptance / done 即视为通过（具体落到 testing 或
            # ready_for_execution 由 sequence 决定，不强测）。
            self.assertNotIn(final_stage, ("acceptance", "done"))
            self.assertTrue(final_stage)


class FfAutoAcceptDispatchTests(unittest.TestCase):
    def test_auto_accept_low_acks_low_risk_decisions(self) -> None:
        """auto_accept='low' → low 自动 ack 不调 input；high 交互 mock 返回 y。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_requirement_repo(root, "req-99")
            append_decision(root, "req-99", _dp(id_="dec-001", risk="low"))
            append_decision(
                root,
                "req-99",
                _dp(id_="dec-002", risk="high", description="高风险但不命中阻塞"),
            )

            with patch("builtins.input", return_value="y") as mock_input:
                rc = workflow_ff_auto(
                    root,
                    auto_accept="low",
                    output_writer=lambda m: None,
                )
            self.assertEqual(rc, 0)
            # 应当只对 high 决策点交互一次；low 自动 ack 不调 input。
            self.assertEqual(mock_input.call_count, 1)

    def test_auto_accept_all_skips_all_interactions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_requirement_repo(root, "req-99")
            append_decision(root, "req-99", _dp(id_="dec-001", risk="low"))
            append_decision(
                root,
                "req-99",
                _dp(id_="dec-002", risk="medium", description="非阻塞中风险"),
            )

            with patch("builtins.input") as mock_input:
                rc = workflow_ff_auto(
                    root,
                    auto_accept="all",
                    output_writer=lambda m: None,
                )
            self.assertEqual(rc, 0)
            # 全部自动 ack，不应触发 input（两条决策都不命中阻塞）。
            self.assertEqual(mock_input.call_count, 0)

    def test_no_auto_accept_flag_requires_all_interaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_requirement_repo(root, "req-99")
            append_decision(root, "req-99", _dp(id_="dec-001", risk="low"))
            append_decision(root, "req-99", _dp(id_="dec-002", risk="medium"))
            append_decision(root, "req-99", _dp(id_="dec-003", risk="low"))

            with patch("builtins.input", return_value="y") as mock_input:
                rc = workflow_ff_auto(
                    root,
                    auto_accept=None,
                    output_writer=lambda m: None,
                )
            self.assertEqual(rc, 0)
            # 默认 mode 下每条决策点都应进交互。
            self.assertEqual(mock_input.call_count, 3)


class FfAutoSummaryTests(unittest.TestCase):
    def test_summary_written_before_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _bootstrap_requirement_repo(root, "req-99")
            append_decision(root, "req-99", _dp(id_="dec-001", risk="low"))

            rc = workflow_ff_auto(root, auto_accept="all", output_writer=lambda m: None)
            self.assertEqual(rc, 0)

            summary = (
                root
                / "artifacts"
                / "main"
                / "requirements"
                / "req-99-demo"
                / "决策汇总.md"
            )
            self.assertTrue(summary.exists())
            text = summary.read_text(encoding="utf-8")
            self.assertIn("决策汇总", text)
            self.assertIn("dec-001", text)

            # stage 已被推进，但仍 < acceptance。
            runtime = load_requirement_runtime(root)
            self.assertNotIn(str(runtime.get("stage", "")), ("acceptance", "done"))


class FfAutoHelperTests(unittest.TestCase):
    def test_should_auto_ack_matrix(self) -> None:
        low = _dp(id_="dec-001", risk="low")
        med = _dp(id_="dec-002", risk="medium")
        hi = _dp(id_="dec-003", risk="high")

        # None → 全交互
        self.assertFalse(_should_auto_ack(low, None))
        self.assertFalse(_should_auto_ack(med, None))
        self.assertFalse(_should_auto_ack(hi, None))
        # "low" → 仅 low 自动
        self.assertTrue(_should_auto_ack(low, "low"))
        self.assertFalse(_should_auto_ack(med, "low"))
        self.assertFalse(_should_auto_ack(hi, "low"))
        # "all" → 全自动
        self.assertTrue(_should_auto_ack(low, "all"))
        self.assertTrue(_should_auto_ack(med, "all"))
        self.assertTrue(_should_auto_ack(hi, "all"))

    def test_check_blocking_before_action_hits_rm_rf(self) -> None:
        self.assertTrue(check_blocking_before_action("准备 rm -rf build/ 目录", ["confirm"]))
        self.assertFalse(check_blocking_before_action("调整文案：把 label 改为 '保存'", ["A", "B"]))


if __name__ == "__main__":
    unittest.main()
