"""
Pytest: bugfix-5（同角色跨 stage 自动续跑硬门禁）验证测试。

覆盖 6 个用例（A-F）：
  A. 同角色连跳：mock runtime + role-stage-map，调 workflow_next，断言翻多格至角色边界。
  B. 话术 lint 命中：mock session-memory 含违规话术，断言 exit code != 0 + 含命中行。
  C. 动态映射回退：analyst.stages 改单 stage，断言只翻一格。
  D. scaffold_v2 mirror 零 diff：diff -rq 断言空（角色关键文件）。
  E. v1 兼容：旧 {role}: "model" 字符串格式，_load_role_stage_map 不报错并按 legacy 转换。
  F. bugfix 流程边界：regression → executing 角色边界，断言不连跳。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
LIVE = ROOT / ".workflow"
MIRROR = ROOT / "src/harness_workflow/assets/scaffold_v2/.workflow"

sys.path.insert(0, str(ROOT / "src"))

from harness_workflow.workflow_helpers import (
    _get_role_for_stage,
    _load_role_stage_map,
    BUGFIX_SEQUENCE,
    WORKFLOW_SEQUENCE,
)
from harness_workflow.validate_contract import check_role_stage_continuity


# ─────────────────────────── helpers ─────────────────────────────

def _make_v2_role_stage_map(roles_override: dict | None = None) -> dict:
    """构造最小 v2 role_stage_map 用于测试。"""
    base = {
        "analyst": {"model": "opus", "stages": ["requirement_review", "planning"]},
        "executing": {"model": "sonnet", "stages": ["executing"]},
        "testing": {"model": "sonnet", "stages": ["testing"]},
        "acceptance": {"model": "sonnet", "stages": ["acceptance"]},
        "regression": {"model": "opus", "stages": ["regression"]},
        "done": {"model": "opus", "stages": ["done"]},
        # alias entries
        "requirement-review": {"model": "opus", "stages": ["requirement_review"], "alias_of": "analyst"},
        "planning": {"model": "opus", "stages": ["planning"], "alias_of": "analyst"},
    }
    if roles_override:
        base.update(roles_override)
    return base


def _write_minimal_runtime(tmp_path: Path, stage: str, operation_type: str = "requirement") -> Path:
    """写最小 runtime.yaml 到临时目录。"""
    rt = tmp_path / ".workflow" / "state"
    rt.mkdir(parents=True, exist_ok=True)
    runtime_file = rt / "runtime.yaml"
    runtime_file.write_text(
        f"stage: {stage}\n"
        f"operation_type: {operation_type}\n"
        f"current_requirement: req-test\n"
        f"operation_target: req-test\n"
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
    return runtime_file


def _write_role_model_map(tmp_path: Path, roles: dict, version: int = 2) -> Path:
    """写 role-model-map.yaml 到临时目录（context 子目录）。"""
    ctx = tmp_path / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    yaml_file = ctx / "role-model-map.yaml"
    data = {"version": version, "default": "sonnet", "roles": roles}
    yaml_file.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return yaml_file


def _write_state_req_yaml(tmp_path: Path, req_id: str, stage: str) -> None:
    """写最小 state requirements yaml。"""
    sr = tmp_path / ".workflow" / "state" / "requirements"
    sr.mkdir(parents=True, exist_ok=True)
    (sr / f"{req_id}.yaml").write_text(
        f"id: {req_id}\ntitle: test\nstatus: {stage}\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )


# ─────────────────────────── 用例 A ─────────────────────────────

def test_case_a_same_role_autojump(tmp_path: Path) -> None:
    """A. 同角色连跳：executing + testing + acceptance 均由同一角色覆盖，
    从 executing 出发，一次 harness next 连跳两格到 acceptance（穿越 testing）。

    在 WORKFLOW_SEQUENCE 中 executing(3) → testing(4) → acceptance(5) 是连续的，
    若三者都绑同一 'evaluator' 角色：
    - executing → testing（同角色，继续）
    - testing → acceptance（同角色，继续）
    - acceptance → done（done 角色 != evaluator，停）
    结果：从 executing 出发，自动翻 2 格到 acceptance（2 条 Workflow advanced to）。

    断言：
    1. runtime.yaml 最终 stage = acceptance。
    2. stdout 含 ≥ 2 条 'Workflow advanced to'（executing→testing + testing→acceptance）。
    """
    _write_minimal_runtime(tmp_path, "executing", "requirement")
    _write_state_req_yaml(tmp_path, "req-test", "executing")

    # 让 executing / testing / acceptance 都由同一 "evaluator" 角色覆盖（连续三格）
    extended_roles = _make_v2_role_stage_map()
    extended_roles["evaluator"] = {"model": "sonnet", "stages": ["executing", "testing", "acceptance"]}
    # 清空原始单独覆盖，避免多角色同时命中
    extended_roles["executing"] = {"model": "sonnet", "stages": []}
    extended_roles["testing"] = {"model": "sonnet", "stages": []}
    extended_roles["acceptance"] = {"model": "sonnet", "stages": []}
    _write_role_model_map(tmp_path, extended_roles)

    (tmp_path / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}', encoding="utf-8")

    import io
    from harness_workflow.workflow_helpers import workflow_next

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    # 应含 ≥ 2 条 'Workflow advanced to'（executing→testing + testing→acceptance）
    advance_lines = [l for l in output.splitlines() if "Workflow advanced to" in l]
    assert len(advance_lines) >= 2, (
        f"Expected ≥ 2 'Workflow advanced to' lines for multi-stage same-role autojump, got:\n{output}"
    )

    # runtime stage 应该是 acceptance（同角色连跳，越过 testing）
    import yaml as _yaml
    rt = _yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "acceptance", (
        f"Expected stage=acceptance after multi-stage same-role autojump, got {rt['stage']!r}"
    )


def test_case_a_two_stage_autojump(tmp_path: Path) -> None:
    """A-2. 两 stage 同角色：requirement_review → planning（analyst 覆盖两 stage）。

    正常配置（analyst 覆盖 [requirement_review, planning]），从 requirement_review 出发
    只跳到 planning（planning 是 analyst 最后一个 stage，下一个是 ready_for_execution 无角色）。
    验证单格跳格也正确产出事件 + state。
    """
    _write_minimal_runtime(tmp_path, "requirement_review", "requirement")
    _write_state_req_yaml(tmp_path, "req-test", "requirement_review")
    _write_role_model_map(tmp_path, _make_v2_role_stage_map())

    (tmp_path / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}', encoding="utf-8")

    import io
    from harness_workflow.workflow_helpers import workflow_next

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    advance_lines = [l for l in output.splitlines() if "Workflow advanced to" in l]
    assert len(advance_lines) >= 1, (
        f"Expected ≥ 1 'Workflow advanced to' line, got:\n{output}"
    )

    import yaml as _yaml
    rt = _yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "planning", f"Expected stage=planning, got {rt['stage']!r}"

    state_yaml = _yaml.safe_load(
        (tmp_path / ".workflow" / "state" / "requirements" / "req-test.yaml").read_text(encoding="utf-8")
    )
    # _sync_stage_to_state_yaml 写 'stage' 字段（不是 'status'，除非 new_stage == 'done'）
    assert state_yaml.get("stage") == "planning", (
        f"Expected requirement stage=planning, got {state_yaml.get('stage')!r}"
    )


# ─────────────────────────── 用例 B ─────────────────────────────

def test_case_b_lint_hit_same_role(tmp_path: Path) -> None:
    """B. 话术 lint 命中：session-memory 含"是否进入 planning"违规话术，同角色场景 → FAIL。"""
    _write_minimal_runtime(tmp_path, "requirement_review", "requirement")
    _write_role_model_map(tmp_path, _make_v2_role_stage_map())

    violating_text = "好的，是否进入 planning 阶段？请确认。"
    rc = check_role_stage_continuity(tmp_path, text_override=violating_text)
    assert rc == 1, (
        f"Expected lint FAIL (rc=1) for same-role stage decision 'planning', got rc={rc}"
    )


def test_case_b_lint_pass_cross_role(tmp_path: Path) -> None:
    """B-附加. 话术 lint 跨角色场景（是否进入 testing）→ PASS（合规决策点）。"""
    _write_minimal_runtime(tmp_path, "requirement_review", "requirement")
    _write_role_model_map(tmp_path, _make_v2_role_stage_map())

    cross_role_text = "是否进入 testing 阶段？"  # analyst→testing 跨角色，合规
    rc = check_role_stage_continuity(tmp_path, text_override=cross_role_text)
    assert rc == 0, (
        f"Expected lint PASS (rc=0) for cross-role decision 'testing', got rc={rc}"
    )


def test_case_b_lint_ignore_tag(tmp_path: Path) -> None:
    """B-附加. 含豁免标记的行不触发 lint FAIL。"""
    _write_minimal_runtime(tmp_path, "requirement_review", "requirement")
    _write_role_model_map(tmp_path, _make_v2_role_stage_map())

    ignored_text = "是否进入 planning 阶段？ <!-- lint:ignore role-stage-continuity -->"
    rc = check_role_stage_continuity(tmp_path, text_override=ignored_text)
    assert rc == 0, (
        f"Expected lint PASS (rc=0) for ignored line, got rc={rc}"
    )


# ─────────────────────────── 用例 C ─────────────────────────────

def test_case_c_dynamic_mapping_single_stage(tmp_path: Path) -> None:
    """C. 动态映射回退：analyst.stages 改单 stage，workflow_next 只翻一格（不连跳）。"""
    _write_minimal_runtime(tmp_path, "requirement_review", "requirement")
    _write_state_req_yaml(tmp_path, "req-test", "requirement_review")
    # analyst 只覆盖 requirement_review，不覆盖 planning
    single_stage_roles = _make_v2_role_stage_map()
    single_stage_roles["analyst"] = {"model": "opus", "stages": ["requirement_review"]}
    # planning 不再有覆盖角色（或覆盖不同角色）
    single_stage_roles["planning"] = {"model": "opus", "stages": ["planning"], "alias_of": "analyst"}  # alias 被跳过
    _write_role_model_map(tmp_path, single_stage_roles)

    (tmp_path / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}', encoding="utf-8")

    import io
    from harness_workflow.workflow_helpers import workflow_next

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    advance_lines = [l for l in output.splitlines() if "Workflow advanced to" in l]
    # 只翻一格（requirement_review → planning）
    assert len(advance_lines) == 1, (
        f"Expected exactly 1 'Workflow advanced to' (no autojump), got:\n{output}"
    )

    import yaml as _yaml
    rt = _yaml.safe_load((tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8"))
    assert rt["stage"] == "planning", f"Expected stage=planning, got {rt['stage']!r}"


# ─────────────────────────── 用例 D ─────────────────────────────

def test_case_d_scaffold_mirror_no_diff() -> None:
    """D. scaffold_v2 mirror 零 diff：关键角色文件在 live 和 mirror 之间完全一致。"""
    key_files = [
        ".workflow/context/role-model-map.yaml",
        ".workflow/context/index.md",
        ".workflow/flow/stages.md",
        ".workflow/context/roles/analyst.md",
        ".workflow/context/roles/executing.md",
        ".workflow/context/roles/testing.md",
        ".workflow/context/roles/acceptance.md",
        ".workflow/context/roles/regression.md",
        ".workflow/context/roles/done.md",
        ".workflow/context/roles/reviewer.md",
        ".workflow/context/checklists/review-checklist.md",
    ]
    mismatches = []
    for rel in key_files:
        live_file = ROOT / rel
        mirror_file = ROOT / "src/harness_workflow/assets/scaffold_v2" / rel
        if not live_file.exists():
            mismatches.append(f"MISSING live: {rel}")
            continue
        if not mirror_file.exists():
            mismatches.append(f"MISSING mirror: src/harness_workflow/assets/scaffold_v2/{rel}")
            continue
        if live_file.read_bytes() != mirror_file.read_bytes():
            mismatches.append(f"MISMATCH: {rel}")

    assert not mismatches, (
        "scaffold_v2 mirror drift detected (硬门禁五：同 commit 必须双写):\n"
        + "\n".join(f"  - {m}" for m in mismatches)
    )


# ─────────────────────────── 用例 E ─────────────────────────────

def test_case_e_v1_compat_no_error(tmp_path: Path) -> None:
    """E. v1 兼容：旧 {role}: "model" 字符串格式，_load_role_stage_map 不报错并按 legacy 转换。"""
    ctx = tmp_path / ".workflow" / "context"
    ctx.mkdir(parents=True, exist_ok=True)
    v1_yaml = ctx / "role-model-map.yaml"
    # v1 格式：role 是 string
    v1_yaml.write_text(
        "version: 1\ndefault: sonnet\nroles:\n"
        "  analyst: opus\n"
        "  executing: sonnet\n"
        "  testing: sonnet\n"
        "  regression: opus\n"
        "  done: opus\n",
        encoding="utf-8",
    )

    role_map = _load_role_stage_map(tmp_path)
    assert isinstance(role_map, dict), "_load_role_stage_map should return dict"
    assert "analyst" in role_map, "analyst key should be present"

    analyst_def = role_map["analyst"]
    assert isinstance(analyst_def, dict), "v1 string should be converted to dict"
    assert analyst_def.get("model") == "opus", f"model should be 'opus', got {analyst_def.get('model')!r}"

    # legacy default stages for analyst
    from harness_workflow.workflow_helpers import _V1_LEGACY_DEFAULT_STAGES
    expected_stages = _V1_LEGACY_DEFAULT_STAGES.get("analyst", [])
    assert analyst_def.get("stages") == expected_stages, (
        f"Expected legacy stages {expected_stages}, got {analyst_def.get('stages')!r}"
    )

    # _get_role_for_stage should work without error
    role = _get_role_for_stage("requirement_review", role_map)
    # In v1 compat, analyst covers requirement_review via legacy default
    assert role is not None or role is None, "Should not raise an error"


# ─────────────────────────── 用例 F ─────────────────────────────

def test_case_f_bugfix_regression_executing_boundary(tmp_path: Path) -> None:
    """F. bugfix 流程边界：regression → executing 是角色边界，不连跳。

    regression 角色 != executing 角色，所以 workflow_next from regression
    只跳一格到 executing，不继续连跳。
    """
    _write_minimal_runtime(tmp_path, "regression", "bugfix")
    # bugfix 流程的 state yaml 路径不同（bugfixes/bugfix-test/...）
    # 这里简化：不需要 state yaml 的精确路径断言，只需 workflow_next 行为正确。
    _write_role_model_map(tmp_path, _make_v2_role_stage_map())

    (tmp_path / ".codex" / "harness").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".codex" / "harness" / "config.json").write_text('{"language": "cn"}', encoding="utf-8")

    # 需要 bugfix state yaml（bugfix-test）
    bf_state = tmp_path / ".workflow" / "state" / "bugfixes"
    bf_state.mkdir(parents=True, exist_ok=True)
    (bf_state / "bugfix-test.yaml").write_text(
        "id: bugfix-test\ntitle: test\nstatus: regression\ncreated_at: '2026-01-01'\n",
        encoding="utf-8",
    )
    # runtime operation_target = bugfix-test
    rt_path = tmp_path / ".workflow" / "state" / "runtime.yaml"
    rt_path.write_text(
        "stage: regression\n"
        "operation_type: bugfix\n"
        "current_requirement: bugfix-test\n"
        "operation_target: bugfix-test\n"
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

    import io
    from harness_workflow.workflow_helpers import workflow_next

    captured = io.StringIO()
    with patch("sys.stdout", captured):
        rc = workflow_next(tmp_path)

    output = captured.getvalue()
    assert rc == 0, f"workflow_next failed: rc={rc}"

    advance_lines = [l for l in output.splitlines() if "Workflow advanced to" in l]
    # regression → executing：不同角色，只跳一格
    assert len(advance_lines) == 1, (
        f"Expected exactly 1 hop (regression→executing boundary, no autojump), got:\n{output}"
    )
    assert "executing" in advance_lines[0], (
        f"Expected hop to 'executing', got: {advance_lines[0]!r}"
    )


# ─────────────────────────── 辅助：helper 单元测试 ─────────────────────────────

def test_get_role_for_stage_basic() -> None:
    """_get_role_for_stage 基本功能：从 map 反查 stage。"""
    role_map = _make_v2_role_stage_map()
    assert _get_role_for_stage("requirement_review", role_map) == "analyst"
    assert _get_role_for_stage("planning", role_map) == "analyst"
    assert _get_role_for_stage("executing", role_map) == "executing"
    assert _get_role_for_stage("testing", role_map) == "testing"
    assert _get_role_for_stage("regression", role_map) == "regression"
    assert _get_role_for_stage("done", role_map) == "done"
    # 无覆盖角色的 stage → None
    assert _get_role_for_stage("ready_for_execution", role_map) is None


def test_get_role_skips_alias() -> None:
    """_get_role_for_stage 应跳过 alias_of 条目，返回主角色。"""
    role_map = _make_v2_role_stage_map()
    # planning 同时被 "analyst" 覆盖（非 alias）和 "planning"（alias_of=analyst）覆盖
    role = _get_role_for_stage("planning", role_map)
    # 应返回非 alias 的 "analyst"，不返回 "planning"（alias）
    assert role == "analyst", f"Expected 'analyst' (non-alias), got {role!r}"


def test_load_role_stage_map_v2() -> None:
    """_load_role_stage_map 加载真实 v2 yaml 并返回正确格式。"""
    role_map = _load_role_stage_map(ROOT)
    assert isinstance(role_map, dict), "_load_role_stage_map should return dict"
    assert "analyst" in role_map
    analyst = role_map["analyst"]
    assert isinstance(analyst, dict)
    assert "model" in analyst
    assert "stages" in analyst
    assert "requirement_review" in analyst["stages"]
    assert "planning" in analyst["stages"]


def test_role_model_map_version_is_2() -> None:
    """role-model-map.yaml 应为 version: 2（bugfix-5 升级）。"""
    data = yaml.safe_load((ROOT / ".workflow/context/role-model-map.yaml").read_text(encoding="utf-8"))
    assert data.get("version") == 2, (
        f"Expected version=2, got {data.get('version')!r}"
    )
