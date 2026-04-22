"""`harness ff --auto` 自主推进器（req-29 / chg-04）。

本模块只负责 **CLI 入口层**：在现有 `harness_ff` 单步 ff 的基础上扩展
`--auto` / `--auto-accept` 语义，把 `current_requirement` 从当前 stage
自动推进到 `acceptance` **前一步**停下，期间：

- 读取 chg-03 `decision_log` 里已经积累的 ``DecisionPoint``（本模块**不**
  自己产生决策点，真正的决策点由上层 subagent 在各 stage 中调用
  ``append_decision`` 写入）；
- 按 5.3 `--auto-accept` 三档语义对每条决策点做"自动 ack / 交互"分档；
- 进入 `acceptance` 之前一次性调 ``write_decision_summary`` 把汇总落到
  ``artifacts/{branch}/requirements/{req-id}-{slug}/决策汇总.md``。

与 5.1 阻塞类别相关的 ``check_blocking_before_action`` helper 在此导出，
供 subagent 在**产出**决策点之前做前置自检；本函数**不**强行把所有
stage 的动作都拦下来，因为 stage 内部没有统一的 action 流可供 hook
（由 stage 角色自觉调用）。

依赖:
- ``decision_log`` 提供 ``DecisionPoint`` / ``append_decision`` /
  ``read_decision_log`` / ``render_decision_summary`` /
  ``write_decision_summary`` / ``is_blocking_decision``；
- ``workflow_helpers`` 提供 ``load_requirement_runtime`` /
  ``save_requirement_runtime`` / ``_sync_stage_to_state_yaml`` 及三条
  stage sequence（WORKFLOW_SEQUENCE / BUGFIX_SEQUENCE / SUGGESTION_SEQUENCE）。
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from harness_workflow.decision_log import (
    DecisionPoint,
    is_blocking_decision,
    read_decision_log,
    write_decision_summary,
)


# ---------------------------------------------------------------------------
# 阻塞前置自检 helper（给 subagent 在产出决策点前调用）
# ---------------------------------------------------------------------------
def check_blocking_before_action(description: str, options: list[str] | None = None) -> bool:
    """判断某个即将写入的决策是否会命中 5.1 阻塞类别。

    便捷 wrapper，内部构造一个临时 ``DecisionPoint`` 调 ``is_blocking_decision``。
    本 helper 不写任何日志，也不终止进程；调用方自己决定"停下等人"的路由。

    Returns
    -------
    bool
        ``True`` 表示命中阻塞类别，调用方应当停下等人并打印原因；
        ``False`` 表示可以继续 ``append_decision``。
    """
    probe = DecisionPoint(
        id="",
        timestamp="",
        stage="",
        risk="high",
        description=description or "",
        options=list(options or []),
        choice="",
        reason="",
    )
    return is_blocking_decision(probe)


# ---------------------------------------------------------------------------
# 三档 ack 逻辑
# ---------------------------------------------------------------------------
def _should_auto_ack(point: DecisionPoint, auto_accept: Optional[str]) -> bool:
    """按 5.3 三档语义判断某条决策点是否应当被自动 ack。

    - ``None`` → 永远返回 ``False``（全交互）
    - ``"low"`` → 仅 ``risk == "low"`` 返回 ``True``
    - ``"all"`` → 恒 ``True``
    """
    if auto_accept is None:
        return False
    if auto_accept == "all":
        return True
    if auto_accept == "low":
        return (point.risk or "").strip().lower() == "low"
    # 未知档位按最保守策略处理：不自动 ack。
    return False


def _default_input_reader(prompt: str) -> str:
    """默认从 stdin 读一行；测试里用 ``unittest.mock.patch('builtins.input')`` 替换。"""
    return input(prompt)


def _interactive_ack(
    point: DecisionPoint,
    input_reader: Callable[[str], str],
    output_writer: Callable[[str], None],
) -> bool:
    """与用户交互确认一条决策点。

    - 打印决策点关键信息；
    - 读 ``y/n``（默认 ``n``）；
    - 返回 ``True`` 表示用户 ack，``False`` 表示拒绝。
    """
    output_writer(f"[ff --auto] 决策点 {point.id} (risk={point.risk}) 需要人工确认")
    output_writer(f"  描述：{point.description}")
    output_writer(f"  选择：{point.choice}")
    output_writer(f"  理由：{point.reason}")
    raw = input_reader("确认通过？(y/N) ").strip().lower()
    return raw in ("y", "yes")


# ---------------------------------------------------------------------------
# stage 推进工具
# ---------------------------------------------------------------------------
def _select_sequence(operation_type: str) -> list[str]:
    """根据 operation_type 返回对应的 stage sequence。

    延迟 import，避免在模块加载阶段引入 ``workflow_helpers`` 的循环依赖。
    """
    from harness_workflow.workflow_helpers import (
        BUGFIX_SEQUENCE,
        SUGGESTION_SEQUENCE,
        WORKFLOW_SEQUENCE,
    )

    op = (operation_type or "").strip()
    if op == "bugfix":
        return list(BUGFIX_SEQUENCE)
    if op == "suggestion":
        return list(SUGGESTION_SEQUENCE)
    return list(WORKFLOW_SEQUENCE)


def _advance_to_stage_before_acceptance(root: Path) -> tuple[str, str]:
    """把 runtime.yaml 的 stage 从当前值推进到 ``acceptance`` 前一步。

    - 若当前 stage 已经等于 ``acceptance`` 或 ``done``，不改动 stage；
    - 若 sequence 中不包含 ``acceptance``（例如 suggestion 流），推到最后一个
      非 ``done`` stage；
    - 返回 ``(from_stage, to_stage)`` 供外层日志使用。
    """
    from harness_workflow.workflow_helpers import (
        load_requirement_runtime,
        save_requirement_runtime,
        _sync_stage_to_state_yaml,
    )

    runtime = load_requirement_runtime(root)
    from_stage = str(runtime.get("stage", "")).strip()
    operation_type = str(runtime.get("operation_type", "")).strip()
    operation_target = str(runtime.get("operation_target", "")).strip()
    if not operation_target:
        operation_target = str(runtime.get("current_requirement", "")).strip()

    sequence = _select_sequence(operation_type)

    # 目标 stage：acceptance 前一步；若 sequence 无 acceptance，取 -2（避开 done）。
    if "acceptance" in sequence:
        target_idx = sequence.index("acceptance") - 1
    else:
        target_idx = max(0, len(sequence) - 2)
    target_idx = max(0, target_idx)
    target_stage = sequence[target_idx]

    # 已经越过目标，则原地不动（不倒退）。
    try:
        current_idx = sequence.index(from_stage) if from_stage in sequence else -1
    except ValueError:
        current_idx = -1
    if current_idx >= target_idx:
        return from_stage, from_stage

    runtime["stage"] = target_stage
    runtime["stage_entered_at"] = datetime.now(timezone.utc).isoformat()
    runtime["ff_mode"] = False

    # req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 4（sug-21）：
    # ff --auto 跳过式推进时，对 sequence 中从 current_idx（含）到 target_idx 的
    # 每个中间 stage 都显式调 _sync_stage_to_state_yaml，保证 bugfix ff 全程
    # stage_timestamps 字段无缺漏。若 current_idx 未定位到（== -1），仅写入 target。
    start = max(0, current_idx) if current_idx >= 0 else target_idx
    for idx in range(start, target_idx + 1):
        _sync_stage_to_state_yaml(root, operation_type, operation_target, sequence[idx])
    save_requirement_runtime(root, runtime)
    return from_stage, target_stage


def _resolve_branch(root: Path) -> str:
    """尽力从 git 或 runtime 里取当前 branch；失败时回退 ``main``。

    artifacts 目录惯例为 ``artifacts/{branch}/requirements/...``；req-29
    仓库实际使用 ``main``，这里不做严格校验，容错优先。
    """
    import subprocess

    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        name = (out.stdout or "").strip()
        if name and name != "HEAD":
            return name
    except Exception:
        pass
    return "main"


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def workflow_ff_auto(
    root: Path,
    auto_accept: Optional[str] = None,
    *,
    input_reader: Callable[[str], str] | None = None,
    output_writer: Callable[[str], None] | None = None,
) -> int:
    """自主推进当前 requirement 到 ``acceptance`` 前一步，期间 ack 决策点。

    Parameters
    ----------
    root:
        仓库根目录。
    auto_accept:
        三档语义：

        - ``None`` 每条决策点都交互；
        - ``"low"`` 仅 ``risk == "low"`` 自动 ack，其余交互；
        - ``"all"`` 全部自动 ack。
    input_reader / output_writer:
        依赖注入的 IO hook，便于测试 mock；未传时默认 ``input`` / ``print``。

    Returns
    -------
    int
        ``0`` 表示自主推进 + 决策 ack 全部通过；非零表示中途被用户拒绝或异常。
    """
    from harness_workflow.workflow_helpers import load_requirement_runtime

    reader = input_reader or _default_input_reader
    writer = output_writer or (lambda msg: print(msg))

    runtime = load_requirement_runtime(root)
    req_id = str(runtime.get("current_requirement", "")).strip()
    if not req_id:
        writer("[ff --auto] 无 current_requirement，退出。")
        return 2

    # 档位合法性（argparse 已兜底，这里再做一层 defensive check）。
    if auto_accept not in (None, "low", "all"):
        writer(f"[ff --auto] 未知 --auto-accept 档位：{auto_accept!r}")
        return 2

    # Step 1：推进 stage 到 acceptance 前一步。
    from_stage, to_stage = _advance_to_stage_before_acceptance(root)
    writer(f"[ff --auto] stage: {from_stage} -> {to_stage}")

    # req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03 扩展：
    # ff --auto 最终落点 stage 派发 briefing，保持与 `harness next --execute` 一致的
    # task_context_index / snapshot 契约。终局 stage（done / archive / completed /
    # ready_for_execution）跳过；原地不动（from == to）也跳过，避免重复派发。
    # 说明：中间 stage 不派发 briefing——ff --auto 的语义是一次性跳过执行，最终落点
    # subagent 才是真正的工作者；若用户需要每个中间 stage 的 briefing，应走
    # `harness next` 逐步推进。
    from harness_workflow.workflow_helpers import (
        _NO_BRIEFING_STAGES,
        _build_subagent_briefing,
        _resolve_title_for_id,
    )

    if to_stage and to_stage != from_stage and to_stage not in _NO_BRIEFING_STAGES:
        req_title = str(runtime.get("current_requirement_title", "")).strip()
        if not req_title:
            req_title = _resolve_title_for_id(root, req_id) or ""
        briefing = _build_subagent_briefing(
            to_stage,
            req_id,
            req_title,
            root=root,
        )
        writer(briefing)

    # Step 2：读 decision_log，按三档 ack。
    decisions = read_decision_log(root, req_id)
    pending_rejected = 0
    for point in decisions:
        if is_blocking_decision(point):
            # 命中 5.1 阻塞类别的决策点不应被自动 ack；即便是 --auto-accept all
            # 也必须交互（req-29 5.1 明确"必须阻塞等人"）。
            writer(f"[ff --auto] 决策点 {point.id} 命中阻塞类别，强制交互。")
            if not _interactive_ack(point, reader, writer):
                pending_rejected += 1
            continue
        if _should_auto_ack(point, auto_accept):
            writer(f"[ff --auto] 自动 ack 决策点 {point.id}（risk={point.risk}）")
            continue
        if not _interactive_ack(point, reader, writer):
            pending_rejected += 1

    # Step 3：落盘决策汇总（无论是否有决策都产出文件，便于对人文档校验）。
    branch = _resolve_branch(root)
    summary_path = write_decision_summary(root, req_id, branch)
    writer(f"[ff --auto] 决策汇总已写入：{summary_path}")

    if pending_rejected:
        writer(f"[ff --auto] 有 {pending_rejected} 条决策被拒绝，acceptance blocked。")
        return 1
    writer("[ff --auto] 所有决策已 ack，可人工进入 acceptance。")
    return 0
