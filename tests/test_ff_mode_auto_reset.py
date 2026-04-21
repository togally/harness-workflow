"""req-31（批量建议合集（20条））/ chg-02（工作流推进 + ff 机制）/ Step 1

覆盖 sug-27（`ff_mode` 在 done / archive 后应自动关闭）：
- `_reset_ff_mode_after_done_archive` helper 在 `new_stage in {done, archive, completed}` 时强制关 `ff_mode`。
- `workflow_next` 翻到 `done` 时 ff_mode 自动降为 False。
- `archive_requirement` 成功后 runtime.yaml 的 `ff_mode` 字段降为 False（AC-自证关键路径）。
- executing 等中间 stage 不误关 ff_mode。
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def test_reset_ff_mode_helper_resets_after_done() -> None:
    from harness_workflow.workflow_helpers import _reset_ff_mode_after_done_archive

    runtime = {"ff_mode": True, "stage": "executing"}
    out = _reset_ff_mode_after_done_archive(runtime, "done")
    assert out["ff_mode"] is False


def test_reset_ff_mode_helper_resets_after_archive() -> None:
    from harness_workflow.workflow_helpers import _reset_ff_mode_after_done_archive

    runtime = {"ff_mode": True}
    out = _reset_ff_mode_after_done_archive(runtime, "archive")
    assert out["ff_mode"] is False


def test_reset_ff_mode_helper_resets_after_completed() -> None:
    from harness_workflow.workflow_helpers import _reset_ff_mode_after_done_archive

    runtime = {"ff_mode": True}
    out = _reset_ff_mode_after_done_archive(runtime, "completed")
    assert out["ff_mode"] is False


def test_reset_ff_mode_helper_preserves_during_executing() -> None:
    from harness_workflow.workflow_helpers import _reset_ff_mode_after_done_archive

    runtime = {"ff_mode": True}
    out = _reset_ff_mode_after_done_archive(runtime, "executing")
    assert out["ff_mode"] is True


def test_reset_ff_mode_helper_noop_when_already_false() -> None:
    from harness_workflow.workflow_helpers import _reset_ff_mode_after_done_archive

    runtime = {"ff_mode": False}
    out = _reset_ff_mode_after_done_archive(runtime, "done")
    assert out["ff_mode"] is False


def test_workflow_next_resets_ff_mode_when_advancing_to_done(tmp_path: Path) -> None:
    """workflow_next 翻到 done 时 ff_mode 自动关。"""
    from harness_workflow.workflow_helpers import (
        load_requirement_runtime,
        save_requirement_runtime,
        workflow_next,
    )

    root = tmp_path
    state = root / ".workflow/state"
    state.mkdir(parents=True)
    (state / "runtime.yaml").write_text(
        "operation_type: requirement\n"
        "operation_target: req-99\n"
        "current_requirement: req-99\n"
        "current_requirement_title: fixture\n"
        "stage: acceptance\n"
        "conversation_mode: open\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "ff_mode: true\n"
        "active_requirements:\n  - req-99\n",
        encoding="utf-8",
    )
    # bare requirement dir (workflow_next only needs runtime + state yaml; 无 state yaml 也可)
    workflow_next(root, execute=False)
    runtime = load_requirement_runtime(root)
    assert runtime.get("stage") == "done"
    assert runtime.get("ff_mode") is False


def test_archive_requirement_resets_ff_mode(tmp_path: Path, monkeypatch) -> None:
    """归档成功后 runtime.yaml 的 ff_mode 自动降为 False（AC-自证关键路径）。"""
    from harness_workflow import workflow_helpers as wh

    root = tmp_path
    # fixture：创建简化 requirement 目录 + runtime + state yaml
    (root / ".workflow").mkdir()
    (root / ".workflow/state").mkdir()
    (root / ".workflow/state/requirements").mkdir()
    (root / ".workflow/state/bugfixes").mkdir()
    (root / "artifacts/main/requirements/req-99-fixture").mkdir(parents=True)
    (root / "artifacts/main/requirements/req-99-fixture/requirement.md").write_text(
        "# req-99（fixture）\n", encoding="utf-8"
    )
    (root / ".workflow/state/requirements/req-99-fixture.yaml").write_text(
        "id: req-99\ntitle: fixture\nstage: done\nstatus: done\n",
        encoding="utf-8",
    )
    (root / ".workflow/state/runtime.yaml").write_text(
        "operation_type: requirement\n"
        "operation_target: req-99\n"
        "current_requirement: req-99\n"
        "current_requirement_title: fixture\n"
        "stage: done\n"
        "conversation_mode: open\n"
        "locked_requirement: ''\n"
        "locked_requirement_title: ''\n"
        "locked_stage: ''\n"
        "current_regression: ''\n"
        "current_regression_title: ''\n"
        "ff_mode: true\n"
        "active_requirements:\n  - req-99\n",
        encoding="utf-8",
    )
    # 跳过 git prompt
    monkeypatch.setattr(wh, "_get_git_branch", lambda _r: "main")
    import builtins
    monkeypatch.setattr(builtins, "input", lambda *a, **k: "n")

    rc = wh.archive_requirement(root, "req-99")
    assert rc == 0
    runtime = wh.load_requirement_runtime(root)
    assert runtime.get("ff_mode") is False, f"ff_mode should be False after archive; got {runtime}"
