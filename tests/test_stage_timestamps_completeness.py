"""req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 2-4

覆盖 sug-16 + sug-21：`_sync_stage_to_state_yaml` 盲区修复 +
regression/bugfix ff 路径 stage_timestamps 字段完整性。

- sug-16：当 state yaml 原本没有 ``stage_timestamps`` 字段时，新版 helper 必须
  自动初始化为空 dict 并写入当前 stage 的时间戳（不再静默跳过）。
- sug-21：`regression_action --testing` 子路径显式触发 sync；bugfix ff 全程每步触发。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _new_root(tmp_path: Path) -> Path:
    (tmp_path / ".workflow/state/requirements").mkdir(parents=True)
    (tmp_path / ".workflow/state/bugfixes").mkdir(parents=True)
    return tmp_path


def test_sync_stage_initializes_missing_timestamps_field(tmp_path: Path) -> None:
    """state yaml 原本无 stage_timestamps 字段时，sync helper 必须自动初始化并写入。"""
    from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml

    root = _new_root(tmp_path)
    yaml_path = root / ".workflow/state/requirements/req-99-x.yaml"
    yaml_path.write_text("id: req-99\ntitle: x\nstage: planning\nstatus: active\n", encoding="utf-8")

    result = _sync_stage_to_state_yaml(root, "requirement", "req-99", "executing")
    assert result == yaml_path
    state = load_simple_yaml(yaml_path)
    assert state.get("stage") == "executing"
    assert isinstance(state.get("stage_timestamps"), dict)
    assert "executing" in state["stage_timestamps"]
    assert state["stage_timestamps"]["executing"]  # 非空 iso 时间戳


def test_sync_stage_preserves_existing_timestamps(tmp_path: Path) -> None:
    """已有 stage_timestamps 时仍保持旧字段，只追加新 stage。"""
    from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml

    root = _new_root(tmp_path)
    yaml_path = root / ".workflow/state/requirements/req-99-x.yaml"
    yaml_path.write_text(
        "id: req-99\ntitle: x\nstage: planning\nstatus: active\n"
        "stage_timestamps:\n  planning: '2026-04-21T00:00:00+00:00'\n",
        encoding="utf-8",
    )
    _sync_stage_to_state_yaml(root, "requirement", "req-99", "testing")
    state = load_simple_yaml(yaml_path)
    assert "planning" in state["stage_timestamps"]
    assert "testing" in state["stage_timestamps"]


def test_sync_stage_noop_for_non_whitelisted_stage(tmp_path: Path) -> None:
    """白名单外 stage（如 apply）不强制写入，避免 schema 漂移。"""
    from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml

    root = _new_root(tmp_path)
    yaml_path = root / ".workflow/state/requirements/req-99-x.yaml"
    yaml_path.write_text("id: req-99\ntitle: x\nstage: apply\nstatus: active\n", encoding="utf-8")

    _sync_stage_to_state_yaml(root, "requirement", "req-99", "apply")
    state = load_simple_yaml(yaml_path)
    assert state.get("stage") == "apply"
    # apply 不在白名单 → 不创建 stage_timestamps
    assert "stage_timestamps" not in state


def test_regression_testing_writes_timestamp(tmp_path: Path, monkeypatch) -> None:
    """regression_action(--testing) 显式触发 sync，state yaml stage_timestamps.testing 非空。"""
    from harness_workflow import workflow_helpers as wh

    root = _new_root(tmp_path)
    (root / ".workflow/state/runtime.yaml").write_text(
        "operation_type: requirement\n"
        "operation_target: req-99\n"
        "current_requirement: req-99\n"
        "current_requirement_title: fixture\n"
        "stage: regression\n"
        "conversation_mode: open\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_regression: reg-01\n"
        "current_regression_title: fixture issue\n"
        "ff_mode: false\n"
        "active_requirements:\n  - req-99\n",
        encoding="utf-8",
    )
    yaml_path = root / ".workflow/state/requirements/req-99-x.yaml"
    yaml_path.write_text("id: req-99\ntitle: x\nstage: regression\nstatus: active\n", encoding="utf-8")
    # _ensure_regression_experience / _update_regression_meta_status 依赖 reg 目录；stub
    monkeypatch.setattr(wh, "_ensure_regression_experience", lambda *a, **k: None)
    monkeypatch.setattr(wh, "_update_regression_meta_status", lambda *a, **k: None)

    rc = wh.regression_action(root, to_testing=True)
    assert rc == 0
    state = wh.load_simple_yaml(yaml_path)
    # sug-16 + sug-21 修复后必须写入 testing 时间戳
    assert isinstance(state.get("stage_timestamps"), dict)
    assert "testing" in state["stage_timestamps"], f"state={state}"


def test_bugfix_ff_writes_multiple_stage_timestamps(tmp_path: Path) -> None:
    """多次调用 _sync_stage 对 bugfix state yaml 叠加时间戳（模拟 bugfix ff 全程）。"""
    from harness_workflow.workflow_helpers import _sync_stage_to_state_yaml, load_simple_yaml

    root = _new_root(tmp_path)
    yaml_path = root / ".workflow/state/bugfixes/bugfix-99.yaml"
    yaml_path.write_text("id: bugfix-99\ntitle: fx\nstage: regression\nstatus: active\n", encoding="utf-8")

    for stage in ("regression", "executing", "testing", "acceptance", "done"):
        _sync_stage_to_state_yaml(root, "bugfix", "bugfix-99", stage)
    state = load_simple_yaml(yaml_path)
    ts = state.get("stage_timestamps") or {}
    for stage in ("regression", "executing", "testing", "acceptance", "done"):
        assert stage in ts, f"missing stage_timestamp for {stage}; got {ts}"


def test_ff_auto_bugfix_advance_writes_path_timestamps(tmp_path: Path, monkeypatch) -> None:
    """workflow_ff_auto 对 bugfix 跳到 target stage 时，经过的每个 stage 都应写入时间戳（sug-21）。

    注：真实 ff_auto 是跳过式推进（_advance_to_stage_before_acceptance 只翻到目标），
    但 Step 4 要求经过的路径 stage 都登记时间戳。本测试只验证 ``executing`` 目标
    调用后 state yaml 的 ``stage_timestamps`` 至少包含 executing。
    """
    from harness_workflow import ff_auto, workflow_helpers as wh

    root = _new_root(tmp_path)
    (root / ".workflow/state/runtime.yaml").write_text(
        "operation_type: bugfix\n"
        "operation_target: bugfix-99\n"
        "current_requirement: bugfix-99\n"
        "current_requirement_title: fx\n"
        "stage: regression\n"
        "conversation_mode: open\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "ff_mode: true\n"
        "active_requirements:\n  - bugfix-99\n",
        encoding="utf-8",
    )
    yaml_path = root / ".workflow/state/bugfixes/bugfix-99.yaml"
    yaml_path.write_text("id: bugfix-99\ntitle: fx\nstage: regression\nstatus: active\n", encoding="utf-8")

    rc = ff_auto.workflow_ff_auto(root, auto_accept="all")
    assert rc == 0
    state = wh.load_simple_yaml(yaml_path)
    ts = state.get("stage_timestamps") or {}
    # bugfix sequence = regression -> executing -> testing -> acceptance -> done
    # target = acceptance 前一步 = testing；经过 regression/executing/testing 三个 stage 都应登记
    assert "testing" in ts, f"state={state}"
    # 覆盖 sug-21 完整性：路径上的 regression & executing 也应登记
    assert "regression" in ts
    assert "executing" in ts
