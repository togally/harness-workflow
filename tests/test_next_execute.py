"""req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 6

覆盖 sug-09（`harness next` 支持触发下一 stage 的实际工作）：
- `workflow_next(execute=True)` 除了翻 stage 外，还 stdout 输出 subagent briefing
  （固定 JSON fence ``` ```subagent-briefing ... ``` ```）供主 agent 直接消费。
- 无 `--execute` 保持原行为，不输出 briefing。
- 翻到 `done` / `archive` 时不输出 briefing（无后续 stage 任务）。
"""
from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _write_runtime(root: Path, stage: str, ff: bool = False) -> None:
    (root / ".workflow/state").mkdir(parents=True, exist_ok=True)
    (root / ".workflow/state/runtime.yaml").write_text(
        f"operation_type: requirement\n"
        f"operation_target: req-99\n"
        f"current_requirement: req-99\n"
        f"current_requirement_title: fixture\n"
        f"stage: {stage}\n"
        f"conversation_mode: open\n"
        f"locked_requirement: ''\n"
        f"locked_requirement_title: ''\n"
        f"locked_stage: ''\n"
        f"current_regression: ''\n"
        f"current_regression_title: ''\n"
        f"ff_mode: {'true' if ff else 'false'}\n"
        f"active_requirements:\n  - req-99\n",
        encoding="utf-8",
    )


def test_next_without_execute_only_advances_no_briefing(tmp_path: Path) -> None:
    from harness_workflow.workflow_helpers import workflow_next

    # P-1 default-pick C（req-31 chg-01）：改测试断言对齐新 stage 序列；planning 替代 changes_review
    _write_runtime(tmp_path, "planning")
    buf = io.StringIO()
    with redirect_stdout(buf):
        workflow_next(tmp_path, execute=False)
    out = buf.getvalue()
    assert "Workflow advanced" in out
    assert "subagent-briefing" not in out


def test_next_execute_outputs_subagent_briefing(tmp_path: Path) -> None:
    from harness_workflow.workflow_helpers import workflow_next

    # P-1 default-pick C（req-31 chg-01）：requirement_review → planning 产 briefing（planning 不在 _NO_BRIEFING_STAGES）
    # 原测试用 changes_review → plan_review；合并后改为 requirement_review → planning
    _write_runtime(tmp_path, "requirement_review")
    buf = io.StringIO()
    with redirect_stdout(buf):
        workflow_next(tmp_path, execute=True)
    out = buf.getvalue()
    assert "```subagent-briefing" in out
    # JSON fence 包含关键字段
    assert "req-99" in out
    assert "fixture" in out  # requirement title
    # 新 stage 为 planning（requirement_review 之后，合并后序列）
    assert "planning" in out


def test_next_execute_does_not_brief_on_done(tmp_path: Path) -> None:
    """翻到 done 时不输出 briefing（无后续 subagent 任务）。"""
    from harness_workflow.workflow_helpers import workflow_next

    _write_runtime(tmp_path, "acceptance", ff=True)
    buf = io.StringIO()
    with redirect_stdout(buf):
        workflow_next(tmp_path, execute=True)
    out = buf.getvalue()
    # acceptance → done；不应输出 briefing
    assert "subagent-briefing" not in out
