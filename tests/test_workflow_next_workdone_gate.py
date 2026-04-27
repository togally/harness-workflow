"""Pytest: req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）。

覆盖 8 用例（4 verdict gate 正负 + 1 same-role 例外 + 1 bugfix 模式 + 1 lint 子命令 + 1 降级）：
  TC-01: executing → testing OK，testing 无 test-report.md 时连跳在 testing 处停下
  TC-02: testing 无 test-report.md → BUG-01 修复：第一格 gate 阻断，stage 保持 testing（不跳 acceptance）
  TC-03: acceptance 无 §结论 → stage 跳到 done（verdict 第一格），while 内 done 是 terminal 自然停
  TC-04: testing 有 test-report.md + acceptance/checklist.md 含 §结论 → 连跳 testing→acceptance→done
  TC-05: requirement_review（analyst 同角色）→ planning，same_role 路径不受 work-done gate 影响
  TC-06: bugfix 模式 testing，test-report.md 缺 → BUG-01 修复：第一格 gate 阻断，stage 保持 testing
  TC-07: `harness validate --contract stage-work-completion`，testing 缺 test-report.md → FAIL + 列缺项
  TC-08: _is_stage_work_done(stage="done", ...) 或未知 stage 返回 True（保守降级）

bugfix-5（同角色跨 stage 自动续跑硬门禁）契约：TC-05 验证 same_role 路径不受 work-done gate 约束。
bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑））契约：testing/acceptance 产物路径同。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from harness_workflow.workflow_helpers import _is_stage_work_done, workflow_next
from harness_workflow.validate_contract import check_stage_work_completion, run_contract_cli


# ─────────────────────────── 公共 fixtures ──────────────────────────────────


def _write_config(root: Path) -> None:
    config_dir = root / ".codex" / "harness"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.json").write_text('{"language": "cn"}', encoding="utf-8")


def _write_role_model_map(root: Path) -> None:
    ctx = root / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    data = {
        "version": 2,
        "default": "sonnet",
        "roles": {
            "analyst": {"model": "opus", "stages": ["requirement_review", "planning"]},
            "executing": {"model": "sonnet", "stages": ["executing"]},
            "testing": {"model": "sonnet", "stages": ["testing"]},
            "acceptance": {"model": "sonnet", "stages": ["acceptance"]},
            "regression": {"model": "opus", "stages": ["regression"]},
            "done": {"model": "opus", "stages": ["done"]},
            "requirement-review": {"model": "opus", "stages": ["requirement_review"], "alias_of": "analyst"},
            "planning": {"model": "opus", "stages": ["planning"], "alias_of": "analyst"},
        },
        "stage_policies": {
            "requirement_review": {"exit_decision": "auto"},
            "planning": {"exit_decision": "user"},
            "ready_for_execution": {"exit_decision": "explicit"},
            "executing": {"exit_decision": "auto"},
            "testing": {"exit_decision": "auto"},
            "acceptance": {"exit_decision": "verdict"},
            "regression": {"exit_decision": "verdict"},
            "done": {"exit_decision": "terminal"},
        },
    }
    (ctx / "role-model-map.yaml").write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")


def _write_runtime(
    root: Path,
    *,
    stage: str,
    operation_type: str = "requirement",
    req_id: str = "req-99",
) -> None:
    state_dir = root / ".workflow" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    runtime = {
        "stage": stage,
        "operation_type": operation_type,
        "current_requirement": req_id,
        "current_requirement_title": "test req",
        "operation_target": req_id,
        "stage_entered_at": "2026-01-01T00:00:00+00:00",
        "conversation_mode": "harness",
        "ff_mode": False,
        "ff_stage_history": [],
        "active_requirements": [req_id],
        "current_regression": "",
        "current_regression_title": "",
        "locked_requirement": "",
        "locked_requirement_title": "",
        "locked_stage": "",
    }
    (state_dir / "runtime.yaml").write_text(yaml.dump(runtime, allow_unicode=True), encoding="utf-8")

    # 写对应的 state yaml（requirements 或 bugfixes）
    if operation_type == "bugfix":
        bf_state_dir = state_dir / "bugfixes"
        bf_state_dir.mkdir(parents=True, exist_ok=True)
        (bf_state_dir / f"{req_id}.yaml").write_text(
            f"id: {req_id}\ntitle: test\nstatus: {stage}\ncreated_at: '2026-01-01'\n",
            encoding="utf-8",
        )
    else:
        req_state_dir = state_dir / "requirements"
        req_state_dir.mkdir(parents=True, exist_ok=True)
        (req_state_dir / f"{req_id}.yaml").write_text(
            f"id: {req_id}\ntitle: test\nstatus: {stage}\ncreated_at: '2026-01-01'\n",
            encoding="utf-8",
        )


def _make_req_tree(
    root: Path,
    req_id: str = "req-99",
    with_test_report: bool = False,
    test_report_has_conclusion: bool = True,
    with_acceptance_checklist: bool = False,
    acceptance_has_conclusion: bool = True,
) -> Path:
    """在 .workflow/flow/requirements/ 下构造 req flow 目录树。"""
    req_flow = root / ".workflow" / "flow" / "requirements" / f"{req_id}-test-req"
    req_flow.mkdir(parents=True, exist_ok=True)

    if with_test_report:
        content = "# test-report\n\n## 结论\n\nPASS\n" if test_report_has_conclusion else "# test-report\n\n内容不含结论段\n"
        (req_flow / "test-report.md").write_text(content, encoding="utf-8")

    if with_acceptance_checklist:
        acc_dir = req_flow / "acceptance"
        acc_dir.mkdir(exist_ok=True)
        content = "# checklist\n\n## 结论\n\n全部通过\n" if acceptance_has_conclusion else "# checklist\n\n无结论段\n"
        (acc_dir / "checklist.md").write_text(content, encoding="utf-8")

    return req_flow


def _make_bugfix_tree(
    root: Path,
    bugfix_id: str = "bugfix-99",
    with_test_report: bool = False,
    test_report_has_conclusion: bool = True,
) -> Path:
    """在 .workflow/flow/bugfixes/ 下构造 bugfix flow 目录树。"""
    bugfix_flow = root / ".workflow" / "flow" / "bugfixes" / f"{bugfix_id}-test-bugfix"
    bugfix_flow.mkdir(parents=True, exist_ok=True)

    if with_test_report:
        content = "# test-report\n\n## 结论\n\nPASS\n" if test_report_has_conclusion else "# test-report\n\n无结论\n"
        (bugfix_flow / "test-report.md").write_text(content, encoding="utf-8")

    return bugfix_flow


# ─────────────────────────── TC-01 ───────────────────────────────────────────


def test_tc01_executing_to_testing_stops_at_testing_when_test_report_missing(tmp_path: Path) -> None:
    """TC-01: executing 出发，testing 缺 test-report.md → while 在 testing 处停下（work-done gate）。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    对应 AC-01。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="executing", req_id=req_id)
    # req flow dir 存在，但 test-report.md 不存在
    _make_req_tree(tmp_path, req_id=req_id, with_test_report=False)

    # 构造 chg-01/session-memory.md 含 ✅（让 executing 自身 work-done gate 通过，翻到 testing）
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test-req"
    chg_dir = req_flow / "changes" / "chg-01-test"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text("## executing\n\n工作完成 ✅\n", encoding="utf-8")
    # tests/ 下有 test_*.py（满足 executing work-done 的第二条件）
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_dummy.py").write_text("# dummy test\n", encoding="utf-8")

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # executing → testing（第一格翻成功）；testing 缺 test-report.md → while 在 testing 停下
    # 最终落点应为 testing（work-done gate 阻断连跳到 acceptance）
    assert rt["stage"] == "testing", (
        f"Expected stage=testing (work-done gate stops at testing), got {rt['stage']!r}\nOutput: {output}"
    )
    assert "Workflow advanced to testing" in output


# ─────────────────────────── TC-02 ───────────────────────────────────────────


def test_tc02_testing_without_test_report_stops_at_testing(tmp_path: Path) -> None:
    """TC-02: runtime stage=testing，test-report.md 不存在 → work-done gate 在第一格前阻断，stage 保持 testing。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    BUG-01 修复：gate 插桩在第一格转换前，testing 缺 test-report.md → 不跳 acceptance。
    对应 AC-02。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="testing", req_id=req_id)
    _make_req_tree(tmp_path, req_id=req_id, with_test_report=False, with_acceptance_checklist=False)

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # BUG-01 修复后：testing 缺 test-report.md → 第一格 gate 阻断 → stage 保持 testing
    assert rt["stage"] == "testing", (
        f"Expected stage=testing (BUG-01 fix: work-done gate before first hop), "
        f"got {rt['stage']!r}\nOutput: {output}"
    )
    # 不应跳到 acceptance 或 done
    assert "Workflow advanced to acceptance" not in output
    assert "Workflow advanced to done" not in output


# ─────────────────────────── TC-03 ───────────────────────────────────────────


def test_tc03_acceptance_without_conclusion_stops_at_acceptance(tmp_path: Path) -> None:
    """TC-03: acceptance checklist.md 缺 §结论 → BUG-01 修复：第一格 gate 阻断，stage 保持 acceptance，不跳 done。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    BUG-01 修复：acceptance 缺 §结论 → _is_stage_work_done=False → 第一格 gate 阻断 → 停在 acceptance。
    对应 AC-03。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="acceptance", req_id=req_id)
    _make_req_tree(
        tmp_path,
        req_id=req_id,
        with_acceptance_checklist=True,
        acceptance_has_conclusion=False,  # 缺 §结论
    )

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # BUG-01 修复后：acceptance exit_decision=verdict，_is_stage_work_done=False → 第一格 gate 阻断
    # stage 保持 acceptance，不跳 done
    assert rt["stage"] == "acceptance", (
        f"Expected stage=acceptance (BUG-01 fix: work-done gate before first hop), "
        f"got {rt['stage']!r}\nOutput: {output}"
    )
    assert "Workflow advanced to done" not in output


# ─────────────────────────── TC-03b ─────────────────────────────────────────


def test_tc03b_acceptance_checklist_conclusion_missing_only_one_hop(tmp_path: Path) -> None:
    """TC-03b（AC-03 核心）：acceptance checklist 缺 §结论 时，harness next 只翻一格（acceptance→done 路径）。

    验证：work-done gate 在 while 循环里针对 from_s=acceptance 阻断继续连跳。
    因 done 本身是 terminal 单格，测试需构造"acceptance 后可能继续跳到更多格"的场景。
    本用例直接验证 _is_stage_work_done 对 acceptance 缺 §结论 返回 False。
    """
    req_id = "req-test-acc"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-slug"
    req_flow.mkdir(parents=True, exist_ok=True)
    acc_dir = req_flow / "acceptance"
    acc_dir.mkdir(exist_ok=True)
    # checklist 存在但缺 §结论
    (acc_dir / "checklist.md").write_text("# checklist\n\n无结论段落\n", encoding="utf-8")

    result = _is_stage_work_done("acceptance", tmp_path, req_id, "requirement")
    assert result is False, (
        f"Expected _is_stage_work_done('acceptance', ...) == False when checklist lacks §结论, got {result!r}"
    )

    # 有 §结论 时应返回 True
    (acc_dir / "checklist.md").write_text("# checklist\n\n## 结论\n\n全部通过\n", encoding="utf-8")
    result2 = _is_stage_work_done("acceptance", tmp_path, req_id, "requirement")
    assert result2 is True, (
        f"Expected _is_stage_work_done('acceptance', ...) == True when checklist has §结论, got {result2!r}"
    )


# ─────────────────────────── TC-04 ───────────────────────────────────────────


def test_tc04_testing_with_artifacts_chains_to_done(tmp_path: Path) -> None:
    """TC-04: testing 有 test-report.md（含结论PASS）+ acceptance/checklist.md（含结论）→ 连跳 testing→acceptance→done。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    对应 AC-04（verdict-driven 连跳保留）。
    bugfix-5（同角色跨 stage 自动续跑硬门禁）/ bugfix-6（工作流契约统一加固（对人机器分离 + 测试契约重塑）） 不退化。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="testing", req_id=req_id)
    _make_req_tree(
        tmp_path,
        req_id=req_id,
        with_test_report=True,
        test_report_has_conclusion=True,
        with_acceptance_checklist=True,
        acceptance_has_conclusion=True,
    )

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: {output}"

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "done", (
        f"Expected stage=done (verdict-driven chain preserved), got {rt['stage']!r}\nOutput: {output}"
    )
    assert "Workflow advanced to done" in output


# ─────────────────────────── TC-05 ───────────────────────────────────────────


def test_tc05_same_role_jump_not_blocked_by_workdone_gate(tmp_path: Path) -> None:
    """TC-05: requirement_review（analyst）→ planning（same_role），planning 产物缺仍可跳。

    bugfix-5（同角色跨 stage 自动续跑硬门禁）契约：same_role 路径不受 work-done gate 约束。
    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）AC-04。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="requirement_review", req_id=req_id)
    # req flow dir 存在但 planning 产物（changes/chg-*/plan.md）缺
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test-req"
    req_flow.mkdir(parents=True, exist_ok=True)

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # requirement_review exit_decision=auto；下一格 planning 是同角色（analyst）
    # same_role 路径：work-done gate 不阻断 → 应翻到 planning
    # planning exit_decision=user → while 停下（user 出口）
    assert rt["stage"] == "planning", (
        f"Expected stage=planning (same_role jump not blocked by work-done gate), "
        f"got {rt['stage']!r}\nOutput: {output}"
    )


# ─────────────────────────── TC-06 ───────────────────────────────────────────


def test_tc06_bugfix_mode_testing_without_report_stops(tmp_path: Path) -> None:
    """TC-06: bugfix 模式 stage=testing，test-report.md 缺 → BUG-01 修复后第一格 gate 阻断，stage 保持 testing。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    BUG-01 修复：gate 插桩在第一格转换前，bugfix 序列同样受 gate 保护。
    对应 AC-01 / AC-02（bugfix 序列同样受保护）。
    """
    bugfix_id = "bugfix-99"
    _write_config(tmp_path)
    _write_role_model_map(tmp_path)
    _write_runtime(tmp_path, stage="testing", operation_type="bugfix", req_id=bugfix_id)
    _make_bugfix_tree(tmp_path, bugfix_id=bugfix_id, with_test_report=False)

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0

    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # BUG-01 修复后：testing 缺 test-report.md → 第一格 gate 阻断 → stage 保持 testing
    assert rt["stage"] == "testing", (
        f"Expected stage=testing (BUG-01 fix: work-done gate before first hop, bugfix mode), "
        f"got {rt['stage']!r}\nOutput: {output}"
    )
    # 不应跳到 acceptance 或 done
    assert "Workflow advanced to acceptance" not in output
    assert "Workflow advanced to done" not in output


# ─────────────────────────── TC-07 ───────────────────────────────────────────


def test_tc07_lint_stage_work_completion_fail_lists_missing(tmp_path: Path) -> None:
    """TC-07: harness validate --contract stage-work-completion，testing 缺 test-report.md → FAIL + 列缺项。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    对应 AC-05（lint 子命令）。
    """
    req_id = "req-99"
    _write_config(tmp_path)
    # 写 runtime.yaml：stage=testing
    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    runtime = {
        "stage": "testing",
        "operation_type": "requirement",
        "current_requirement": req_id,
        "operation_target": req_id,
        "stage_entered_at": "2026-01-01T00:00:00+00:00",
    }
    (state_dir / "runtime.yaml").write_text(yaml.dump(runtime, allow_unicode=True), encoding="utf-8")

    # req flow dir 存在，但 test-report.md 不存在
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test-req"
    req_flow.mkdir(parents=True, exist_ok=True)

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = check_stage_work_completion(tmp_path)

    output = captured.getvalue()
    assert rc == 1, f"Expected FAIL (rc=1) when test-report.md missing, got rc={rc}\nOutput: {output}"
    assert "FAIL" in output
    # 应列出 test-report.md 缺失
    assert "test-report.md" in output

    # 同样通过 run_contract_cli 路由验证
    captured2 = io.StringIO()
    with patch("sys.stdout", captured2):
        rc2 = run_contract_cli(tmp_path, contract="stage-work-completion")
    assert rc2 == 1, f"Expected rc=1 from run_contract_cli stage-work-completion, got {rc2}"


# ─────────────────────────── TC-08 ───────────────────────────────────────────


def test_tc08_fallback_returns_true_for_done_and_unknown_stage(tmp_path: Path) -> None:
    """TC-08: _is_stage_work_done 对 done / 未知 stage / 解析失败返回 True（保守降级）。

    req-45（harness next over-chain bug 修复（紧急））/ chg-01（verdict stage work-done gate + workflow_next 集成）
    对应 AC-04（不阻塞 terminal / regression 出口）。
    """
    # done stage → True
    result = _is_stage_work_done("done", tmp_path, "req-99", "requirement")
    assert result is True, f"Expected True for stage='done', got {result!r}"

    # regression stage → True
    result = _is_stage_work_done("regression", tmp_path, "req-99", "requirement")
    assert result is True, f"Expected True for stage='regression', got {result!r}"

    # 空字符串 stage → True
    result = _is_stage_work_done("", tmp_path, "req-99", "requirement")
    assert result is True, f"Expected True for stage='', got {result!r}"

    # 未知 stage → True
    result = _is_stage_work_done("nonexistent_stage", tmp_path, "req-99", "requirement")
    assert result is True, f"Expected True for unknown stage, got {result!r}"

    # req_id 为空 → True（无法解析）
    result = _is_stage_work_done("testing", tmp_path, "", "requirement")
    assert result is True, f"Expected True when req_id='', got {result!r}"

    # flow dir 不存在时 → True（保守降级）
    result = _is_stage_work_done("testing", tmp_path, "req-nonexistent-xyz-123", "requirement")
    assert result is True, f"Expected True when flow dir not found, got {result!r}"
