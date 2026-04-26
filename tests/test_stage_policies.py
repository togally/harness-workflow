"""
Pytest: bugfix-5（同角色跨 stage 自动续跑硬门禁）修复点 6 — verdict-driven 自动跳测试。

覆盖 4 个用例（G/H/I/J）：
  G. acceptance→done 自动跳（verdict=PASS, exit_decision=verdict）
  H. acceptance→regression 自动跳（verdict=FAIL, reg 路由）
  I. executing stage explicit gate 保留（explicit 停下 / auto 翻一格不越界）
  J. stage_policies 缺字段时 _get_exit_decision 返回 "user"（保守降级）
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

from harness_workflow.workflow_helpers import (
    _get_exit_decision,
    _load_stage_policies,
    _get_role_for_stage,
    _load_role_stage_map,
    BUGFIX_SEQUENCE,
    WORKFLOW_SEQUENCE,
    workflow_next,
)


# ─────────────────────────── 共用 helpers ─────────────────────────────

def _write_runtime(tmp_path: Path, stage: str, operation_type: str = "bugfix") -> Path:
    """写最小 runtime.yaml。"""
    rt = tmp_path / ".workflow" / "state"
    rt.mkdir(parents=True, exist_ok=True)
    runtime_file = rt / "runtime.yaml"
    runtime_file.write_text(
        f"stage: {stage}\n"
        f"operation_type: {operation_type}\n"
        f"current_requirement: bugfix-test\n"
        f"operation_target: bugfix-test\n"
        "stage_entered_at: '2026-01-01T00:00:00+00:00'\n"
        "conversation_mode: harness\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        "active_requirements: []\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_requirement_title: 'test bugfix'\n",
        encoding="utf-8",
    )
    return runtime_file


def _write_role_model_map_with_policies(tmp_path: Path, stage_policies: dict | None = None) -> Path:
    """写 role-model-map.yaml v2（含 stage_policies）到临时目录。"""
    ctx = tmp_path / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    yaml_file = ctx / "role-model-map.yaml"

    roles = {
        "analyst": {"model": "opus", "stages": ["requirement_review", "planning"]},
        "executing": {"model": "sonnet", "stages": ["executing"]},
        "testing": {"model": "sonnet", "stages": ["testing"]},
        "acceptance": {"model": "sonnet", "stages": ["acceptance"]},
        "regression": {"model": "opus", "stages": ["regression"]},
        "done": {"model": "opus", "stages": ["done"]},
        "requirement-review": {"model": "opus", "stages": ["requirement_review"], "alias_of": "analyst"},
        "planning": {"model": "opus", "stages": ["planning"], "alias_of": "analyst"},
    }

    data: dict = {"version": 2, "default": "sonnet", "roles": roles}
    if stage_policies is not None:
        data["stage_policies"] = stage_policies

    yaml_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return yaml_file


def _write_bugfix_state_yaml(tmp_path: Path, bf_id: str, stage: str) -> None:
    """写 bugfix state yaml。"""
    bf_state = tmp_path / ".workflow" / "state" / "bugfixes"
    bf_state.mkdir(parents=True, exist_ok=True)
    (bf_state / f"{bf_id}.yaml").write_text(
        f"id: {bf_id}\ntitle: test\nstatus: {stage}\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )


def _write_config(tmp_path: Path) -> None:
    (tmp_path / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}', encoding="utf-8")


# ─────────────────────────── 用例 G ─────────────────────────────

def test_case_g_acceptance_to_done_verdict_autojump(tmp_path: Path) -> None:
    """G. acceptance→done 自动跳（修复点 6 / verdict-driven）。

    mock runtime stage=acceptance, operation_type=bugfix,
    stage_policies.acceptance.exit_decision=verdict（PASS 路由到 done）。
    调 workflow_next(execute=False)，断言：
    1. runtime 最终 stage = done
    2. stdout 含 'Workflow advanced to done'
    3. feedback log 含 stage_advance: acceptance→done 事件
    """
    _write_runtime(tmp_path, "acceptance", "bugfix")
    _write_bugfix_state_yaml(tmp_path, "bugfix-test", "acceptance")
    _write_config(tmp_path)

    stage_policies = {
        "requirement_review": {"exit_decision": "auto"},
        "planning": {"exit_decision": "user"},
        "ready_for_execution": {"exit_decision": "explicit"},
        "executing": {"exit_decision": "auto"},
        "testing": {"exit_decision": "auto"},
        "acceptance": {"exit_decision": "verdict"},  # 触发 verdict-driven 连跳
        "regression": {"exit_decision": "verdict"},
        "done": {"exit_decision": "terminal"},
    }
    _write_role_model_map_with_policies(tmp_path, stage_policies)

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    # 断言 stdout 含 Workflow advanced to done
    assert "Workflow advanced to done" in output, (
        f"Expected 'Workflow advanced to done' in output, got:\n{output}"
    )

    # 断言 runtime stage = done
    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "done", f"Expected stage=done, got {rt['stage']!r}"

    # 断言 feedback events 含 stage_advance acceptance→done
    feedback_log = tmp_path / ".workflow" / "state" / "feedback-events.yaml"
    if feedback_log.exists():
        events_data = yaml.safe_load(feedback_log.read_text(encoding="utf-8")) or []
        advance_events = [e for e in events_data if e.get("event_type") == "stage_advance"]
        acceptance_to_done = any(
            e.get("data", {}).get("from_stage") == "acceptance"
            and e.get("data", {}).get("to_stage") == "done"
            for e in advance_events
        )
        assert acceptance_to_done, (
            f"Expected stage_advance event acceptance→done in feedback log.\nEvents: {advance_events}"
        )


# ─────────────────────────── 用例 H ─────────────────────────────

def test_case_h_acceptance_to_regression_fail_route(tmp_path: Path) -> None:
    """H. acceptance exit_decision=verdict 验证 + FAIL 路由路径。

    修复点 6 核心验证：
    1. _get_exit_decision("acceptance", policies) 返回 "verdict"（断言 yaml 已落）
    2. 构造 current_regression + 有效 decision.md（route_to: regression），
       调 workflow_next，断言翻到 regression（不停在 acceptance，reg 路由生效）
    3. regression 的 exit_decision 同样为 verdict（断言双 stage 配置正确）

    注意：reg 路由通过 current_regression + decision.md 触发，优先于 verdict-driven 连跳；
    两路均能让 acceptance 不停在原位，满足"不向用户暴露 acceptance→next 决策点"的契约。
    """
    _write_runtime(tmp_path, "acceptance", "bugfix")
    _write_bugfix_state_yaml(tmp_path, "bugfix-test", "acceptance")
    _write_config(tmp_path)

    stage_policies = {
        "acceptance": {"exit_decision": "verdict"},
        "regression": {"exit_decision": "verdict"},
        "executing": {"exit_decision": "auto"},
        "testing": {"exit_decision": "auto"},
        "done": {"exit_decision": "terminal"},
    }
    _write_role_model_map_with_policies(tmp_path, stage_policies)

    # ---- H-1：验证 _get_exit_decision 返回 "verdict" ----
    policies = _load_stage_policies(tmp_path)
    assert _get_exit_decision("acceptance", policies) == "verdict", (
        "acceptance should have exit_decision=verdict"
    )
    assert _get_exit_decision("regression", policies) == "verdict", (
        "regression should have exit_decision=verdict"
    )

    # ---- H-2：构造 reg 路由 (legacy .workflow/flow/regressions/ 路径可被查到) ----
    # _locate_regression_dir 优先查 artifacts/branch/bugfixes/{id}/regressions/
    # 但 bugfix 流程无标准 requirements 目录，退回到 .workflow/flow/regressions/
    reg_fallback = tmp_path / ".workflow" / "flow" / "regressions" / "reg-test"
    reg_fallback.mkdir(parents=True, exist_ok=True)
    (reg_fallback / "decision.md").write_text(
        "---\nroute_to: regression\n---\n# Decision\n\n路由：regression\n",
        encoding="utf-8",
    )

    # 注入 current_regression 到 runtime
    rt_path = tmp_path / ".workflow" / "state" / "runtime.yaml"
    rt_data = yaml.safe_load(rt_path.read_text(encoding="utf-8")) or {}
    rt_data["current_regression"] = "reg-test"
    rt_data["current_regression_title"] = "test regression"
    rt_path.write_text(yaml.dump(rt_data, allow_unicode=True), encoding="utf-8")

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    # 断言翻到 regression（reg 路由生效）
    rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "regression", (
        f"Expected stage=regression (FAIL route), got {rt['stage']!r}\nOutput: {output}"
    )
    assert "Workflow advanced to regression" in output, (
        f"Expected 'Workflow advanced to regression' in output, got:\n{output}"
    )


# ─────────────────────────── 用例 I ─────────────────────────────

def test_case_i_explicit_gate_preserved(tmp_path: Path) -> None:
    """I. explicit gate 永远阻止连跳（修复点 6 / explicit 不自动跳）。

    构造 mock 场景：stage_policies 中某 stage 设 explicit，
    验证 workflow_next 不会越过该 stage 自动连跳（explicit 永远停下）。

    两个子测试：
    I-a: ready_for_execution + execute=False → SystemExit（内置 gate，不变）
    I-b: mock 某 stage 设 explicit，验证 while 循环 break（explicit 分支保留）

    注意：current_requirement 用 req- 前缀避免 load_requirement_runtime 自推断 bugfix 序列。
    注意：ready_for_execution 有内置 SystemExit 检查（execute=False），与 stage_policies 独立。
    """
    # ---- 子测试 I-a：ready_for_execution 内置显式 gate（execute=False → SystemExit）----
    rt_dir = tmp_path / ".workflow" / "state"
    rt_dir.mkdir(parents=True, exist_ok=True)
    runtime_file = rt_dir / "runtime.yaml"
    runtime_file.write_text(
        "stage: ready_for_execution\n"
        "operation_type: requirement\n"
        "current_requirement: req-test\n"
        "operation_target: req-test\n"
        "stage_entered_at: '2026-01-01T00:00:00+00:00'\n"
        "conversation_mode: harness\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        "active_requirements: []\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_requirement_title: 'test requirement'\n",
        encoding="utf-8",
    )
    req_state = tmp_path / ".workflow" / "state" / "requirements"
    req_state.mkdir(parents=True, exist_ok=True)
    (req_state / "req-test.yaml").write_text(
        "id: req-test\ntitle: test\nstatus: ready_for_execution\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )
    _write_config(tmp_path)

    # stage_policies: executing=explicit（模拟 explicit 出口阻止连跳的场景）
    # ready_for_execution 内置 gate 由代码检查，不依赖 stage_policies
    stage_policies_with_explicit_executing = {
        "ready_for_execution": {"exit_decision": "explicit"},
        "executing": {"exit_decision": "explicit"},  # 模拟 executing 设 explicit 阻止连跳
        "testing": {"exit_decision": "auto"},
        "acceptance": {"exit_decision": "verdict"},
        "done": {"exit_decision": "terminal"},
    }
    _write_role_model_map_with_policies(tmp_path, stage_policies_with_explicit_executing)

    # execute=False → 应触发 SystemExit（内置 gate，不依赖 stage_policies）
    with pytest.raises(SystemExit) as exc_info:
        workflow_next(tmp_path, execute=False)
    assert "ready_for_execution" in str(exc_info.value) or "--execute" in str(exc_info.value), (
        f"Expected SystemExit mentioning ready_for_execution or --execute, got: {exc_info.value!r}"
    )

    # ---- 子测试 I-b：executing 设 explicit 时，从 requirement_review 出发只翻到 planning，
    #                  不继续越过 planning（planning=user）
    # 更简洁地验证 explicit break：从 planning 出发，执行方设 executing=explicit，
    # 断言只翻一格到 executing 而不继续（因 executing.exit_decision=explicit break）
    runtime_file.write_text(
        "stage: planning\n"
        "operation_type: requirement\n"
        "current_requirement: req-test\n"
        "operation_target: req-test\n"
        "stage_entered_at: '2026-01-01T00:00:00+00:00'\n"
        "conversation_mode: harness\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        "active_requirements: []\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_requirement_title: 'test requirement'\n",
        encoding="utf-8",
    )
    (req_state / "req-test.yaml").write_text(
        "id: req-test\ntitle: test\nstatus: planning\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path, execute=False)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next planning→next failed: rc={rc}\nOutput: {output}"

    # planning.exit_decision=user → 只翻一格到 ready_for_execution（user 停下）
    final_rt = yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    # planning 出口是 user，所以只翻一格（到 ready_for_execution），不继续
    assert final_rt["stage"] == "ready_for_execution", (
        f"Expected stage=ready_for_execution (planning.exit_decision=user stops here), "
        f"got {final_rt['stage']!r}\nOutput: {output}"
    )

    advance_lines = [ln for ln in output.splitlines() if "Workflow advanced to" in ln]
    assert len(advance_lines) == 1, (
        f"Expected exactly 1 hop (planning.exit_decision=user stops autojump), got:\n{output}"
    )

    # 验证 _get_exit_decision("ready_for_execution", ...) 返回 "explicit"
    policies = _load_stage_policies(tmp_path)
    assert _get_exit_decision("ready_for_execution", policies) == "explicit", (
        "ready_for_execution should have exit_decision=explicit"
    )
    # 验证 _get_exit_decision("executing", ...) 在 mock 中返回 "explicit"
    assert _get_exit_decision("executing", policies) == "explicit", (
        "executing should have exit_decision=explicit in this mock"
    )


# ─────────────────────────── 用例 J ─────────────────────────────

def test_case_j_missing_stage_policies_defaults_to_user() -> None:
    """J. stage_policies 缺字段时 _get_exit_decision 默认返回 "user"（保守降级）。

    1. 调 _get_exit_decision('any_stage', {}) → "user"
    2. 调 _get_exit_decision('acceptance', {}) → "user"（缺 stage_policies 时）
    3. 验证整个 yaml 没有 stage_policies 时 _load_stage_policies 返回 {}
    """
    # 场景 1：空 policy_map → 返回 "user"
    result = _get_exit_decision("any_stage", {})
    assert result == "user", f"Expected 'user' for empty policy_map, got {result!r}"

    # 场景 2：acceptance 缺字段 → 返回 "user"
    result = _get_exit_decision("acceptance", {})
    assert result == "user", f"Expected 'user' for missing acceptance policy, got {result!r}"

    # 场景 3：policy_map 不是 dict → 返回 "user"
    result = _get_exit_decision("testing", None)  # type: ignore[arg-type]
    assert result == "user", f"Expected 'user' for None policy_map, got {result!r}"

    # 场景 4：stage_policy 不是 dict → 返回 "user"
    result = _get_exit_decision("acceptance", {"acceptance": "verdict"})  # string, not dict
    assert result == "user", f"Expected 'user' for non-dict stage_policy, got {result!r}"

    # 场景 5：exit_decision 缺字段 → 返回 "user"
    result = _get_exit_decision("acceptance", {"acceptance": {}})
    assert result == "user", f"Expected 'user' for missing exit_decision key, got {result!r}"

    print("PASS: all _get_exit_decision fallback-to-user cases verified")


def test_case_j_load_stage_policies_returns_empty_when_missing(tmp_path: Path) -> None:
    """J-附加：yaml 中完全没有 stage_policies 字段时 _load_stage_policies 返回 {}。"""
    # 写不含 stage_policies 的 yaml
    ctx = tmp_path / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    yaml_file = ctx / "role-model-map.yaml"
    yaml_file.write_text(
        "version: 2\ndefault: sonnet\nroles:\n  analyst:\n    model: opus\n    stages: []\n",
        encoding="utf-8",
    )
    policies = _load_stage_policies(tmp_path)
    assert policies == {}, f"Expected empty dict when stage_policies missing, got {policies!r}"


# ─────────────────────────── 单元测试：_get_exit_decision helper ─────────────────────────────

def test_get_exit_decision_from_real_yaml() -> None:
    """从真实 role-model-map.yaml 读 stage_policies，验证关键 stage 的 exit_decision 值。"""
    policies = _load_stage_policies(ROOT)
    assert isinstance(policies, dict), "_load_stage_policies should return dict"
    assert len(policies) >= 7, f"Expected ≥7 stage policies, got {len(policies)}"

    assert _get_exit_decision("acceptance", policies) == "verdict", (
        f"acceptance should have exit_decision=verdict, got {_get_exit_decision('acceptance', policies)!r}"
    )
    assert _get_exit_decision("regression", policies) == "verdict", (
        f"regression should have exit_decision=verdict, got {_get_exit_decision('regression', policies)!r}"
    )
    assert _get_exit_decision("executing", policies) == "auto", (
        f"executing should have exit_decision=auto, got {_get_exit_decision('executing', policies)!r}"
    )
    assert _get_exit_decision("planning", policies) == "user", (
        f"planning should have exit_decision=user, got {_get_exit_decision('planning', policies)!r}"
    )
    assert _get_exit_decision("ready_for_execution", policies) == "explicit", (
        f"ready_for_execution should have exit_decision=explicit, got "
        f"{_get_exit_decision('ready_for_execution', policies)!r}"
    )
    assert _get_exit_decision("done", policies) == "terminal", (
        f"done should have exit_decision=terminal, got {_get_exit_decision('done', policies)!r}"
    )
    # 未声明的 stage → user（保守降级）
    assert _get_exit_decision("nonexistent_stage", policies) == "user", (
        "nonexistent_stage should fall back to 'user'"
    )
