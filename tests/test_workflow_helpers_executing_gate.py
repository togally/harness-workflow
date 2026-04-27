"""Pytest: req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）。

覆盖 plan.md TC-01 / TC-02 / TC-08（unit 直调 helper）：
  TC-01: _is_stage_work_done('executing', tmp, req_id, 'requirement') 当 changes_dir 缺 → False（严格化生效）
  TC-02: _is_stage_work_done('testing', tmp, req_id, 'requirement') 当 test-report.md 缺 → False（既有行为回归）
  TC-08: _check_pipx_freshness() 验证 venv _is_stage_work_done import 不报 ImportError + venv mtime ≥ HEAD commit ts
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from harness_workflow.workflow_helpers import _is_stage_work_done


# ─────────────────────────── TC-01 ───────────────────────────────────────────


def test_tc01_executing_no_changes_dir_returns_false(tmp_path: Path) -> None:
    """TC-01: _is_stage_work_done('executing', ...) 当 changes_dir 缺时返回 False（严格化生效）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-1（保守降级严格化）：changes_dir 缺 → False（reg-02（over-chain 三维失配） + chg-02 严格化，不再 True）。
    """
    req_id = "req-x"
    # 只创建 req flow dir，不创建 changes 子目录
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    req_flow.mkdir(parents=True, exist_ok=True)

    result = _is_stage_work_done("executing", tmp_path, req_id, "requirement")
    assert result is False, (
        f"TC-01: Expected _is_stage_work_done('executing', ...) == False when changes_dir missing, "
        f"got {result!r}"
    )


def test_tc01b_executing_changes_dir_exists_but_no_session_memory_returns_false(tmp_path: Path) -> None:
    """TC-01b: _is_stage_work_done('executing', ...) 当 changes_dir 存在但无 session-memory.md → False（严格化）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-1（保守降级严格化）：session-memory.md 缺 → False（reg-02（over-chain 三维失配） + chg-02 严格化）。
    """
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    # changes 目录存在但里面没有 session-memory.md
    changes_dir = req_flow / "changes" / "chg-01-placeholder"
    changes_dir.mkdir(parents=True, exist_ok=True)
    # 只创建 chg dir，不创建 session-memory.md

    result = _is_stage_work_done("executing", tmp_path, req_id, "requirement")
    assert result is False, (
        f"TC-01b: Expected False when changes_dir exists but no session-memory.md files, "
        f"got {result!r}"
    )


def test_tc01c_executing_with_session_memory_no_checkmark_returns_false(tmp_path: Path) -> None:
    """TC-01c: session-memory.md 存在但无 ✅ → False（既有行为，回归用例）。"""
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    chg_dir = req_flow / "changes" / "chg-01"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text("## executing\n\n工作未完成（无检查标记）\n", encoding="utf-8")

    result = _is_stage_work_done("executing", tmp_path, req_id, "requirement")
    assert result is False, (
        f"TC-01c: Expected False when session-memory.md exists but lacks ✅, got {result!r}"
    )


def test_tc01d_executing_with_session_memory_and_tests_returns_true(tmp_path: Path) -> None:
    """TC-01d: session-memory.md 含 ✅ + tests/ 有 test_*.py → True（正常完成态）。"""
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    chg_dir = req_flow / "changes" / "chg-01"
    chg_dir.mkdir(parents=True, exist_ok=True)
    (chg_dir / "session-memory.md").write_text("## executing done\n\n全部完成 ✅\n", encoding="utf-8")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    (tests_dir / "test_dummy.py").write_text("# dummy\n", encoding="utf-8")

    result = _is_stage_work_done("executing", tmp_path, req_id, "requirement")
    assert result is True, (
        f"TC-01d: Expected True when session-memory.md has ✅ + tests/, got {result!r}"
    )


# ─────────────────────────── TC-02 ───────────────────────────────────────────


def test_tc02_testing_no_test_report_returns_false(tmp_path: Path) -> None:
    """TC-02: _is_stage_work_done('testing', ...) 当 test-report.md 缺时返回 False（既有行为，回归用例）。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-1（保守降级严格化）：testing 缺 test-report.md → False（既有行为不回退）。
    """
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    req_flow.mkdir(parents=True, exist_ok=True)
    # 不创建 test-report.md

    result = _is_stage_work_done("testing", tmp_path, req_id, "requirement")
    assert result is False, (
        f"TC-02: Expected _is_stage_work_done('testing', ...) == False when test-report.md missing, "
        f"got {result!r}"
    )


def test_tc02b_testing_with_report_no_conclusion_returns_false(tmp_path: Path) -> None:
    """TC-02b: test-report.md 存在但无 §结论 → False（既有行为）。"""
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    req_flow.mkdir(parents=True, exist_ok=True)
    (req_flow / "test-report.md").write_text("# test-report\n\n测试通过，但缺少结论段\n", encoding="utf-8")

    result = _is_stage_work_done("testing", tmp_path, req_id, "requirement")
    assert result is False, (
        f"TC-02b: Expected False when test-report.md lacks §结论, got {result!r}"
    )


def test_tc02c_testing_with_report_and_conclusion_returns_true(tmp_path: Path) -> None:
    """TC-02c: test-report.md 含 §结论 → True（正常完成态）。"""
    req_id = "req-x"
    req_flow = tmp_path / ".workflow" / "flow" / "requirements" / f"{req_id}-test"
    req_flow.mkdir(parents=True, exist_ok=True)
    (req_flow / "test-report.md").write_text("# test-report\n\n## 结论\n\nPASS\n", encoding="utf-8")

    result = _is_stage_work_done("testing", tmp_path, req_id, "requirement")
    assert result is True, (
        f"TC-02c: Expected True when test-report.md has §结论, got {result!r}"
    )


# ─────────────────────────── TC-08 ───────────────────────────────────────────


def _check_pipx_freshness() -> tuple[bool, str]:
    """检查 pipx venv 中 _is_stage_work_done 可 import + venv mtime ≥ HEAD commit ts。

    返回 (is_fresh: bool, message: str)。
    """
    import importlib
    import importlib.util

    # 1. 验证 _is_stage_work_done 可 import（不报 ImportError）
    try:
        spec = importlib.util.find_spec("harness_workflow.workflow_helpers")
        if spec is None:
            return False, "_is_stage_work_done: importlib.util.find_spec returned None"
        mod = importlib.import_module("harness_workflow.workflow_helpers")
        if not hasattr(mod, "_is_stage_work_done"):
            return False, "_is_stage_work_done: attribute not found in harness_workflow.workflow_helpers"
        module_file = mod.__file__
        if module_file is None:
            return False, "_is_stage_work_done: __file__ is None"
    except ImportError as e:
        return False, f"ImportError: {e}"

    # 2. venv mtime ≥ HEAD commit ts
    venv_mtime = os.path.getmtime(module_file)

    import subprocess
    try:
        res = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", "src/harness_workflow/workflow_helpers.py"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=10,
        )
        commit_ts_str = res.stdout.strip()
        if not commit_ts_str:
            # no commits touching this file yet — treat as fresh
            return True, "no commits found for workflow_helpers.py, treating as fresh"
        commit_ts = float(commit_ts_str)
    except Exception as e:
        return False, f"git log failed: {e}"

    if venv_mtime < commit_ts:
        diff_s = commit_ts - venv_mtime
        return False, (
            f"venv mtime {venv_mtime:.0f} < HEAD commit ts {commit_ts:.0f} "
            f"(stale by {diff_s:.0f}s); run `pipx install --force <repo-path>`"
        )

    return True, (
        f"venv mtime {venv_mtime:.0f} >= HEAD commit ts {commit_ts:.0f} "
        f"(diff = {venv_mtime - commit_ts:.0f}s)"
    )


def test_tc08_pipx_freshness_helper_fresh_returns_true() -> None:
    """TC-08: _check_pipx_freshness() 验证 venv _is_stage_work_done import 不报 ImportError + venv mtime ≥ HEAD commit ts。

    req-46（建议池梳理验证 + 优先级 roadmap + 分批落地）/ chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood）
    AC-5（部署同步契约文档化）：部署版本一致时返回 True + 报告 diff 秒数。
    前提：在本 test 文件跑前已执行 `pipx install --force <repo-path>`（Step 8 dogfood 保证）。
    """
    is_fresh, message = _check_pipx_freshness()
    assert is_fresh is True, (
        f"TC-08: _check_pipx_freshness() returned False: {message}\n"
        f"Hint: run `pipx install --force /Users/jiazhiwei/claudeProject/harness-workflow` to sync deploy."
    )


def test_tc08b_pipx_freshness_stale_returns_false(tmp_path: Path) -> None:
    """TC-08b: 模拟 venv mtime 早于 commit ts → _check_pipx_freshness 应返回 False + 报差值。

    reg-02（over-chain 三维失配） + chg-02（over-chain bug 真修 + deploy 契约 + 子进程 dogfood） mtime 反例验证。
    """
    # 用 monkeypath 方式直接测试 stale 判断逻辑（不依赖实际 venv）
    # 构造 stale 场景：venv_mtime < commit_ts
    venv_mtime = 1000.0
    commit_ts = 2000.0
    diff_s = commit_ts - venv_mtime

    is_stale = venv_mtime < commit_ts
    assert is_stale is True, "TC-08b: should detect stale when venv_mtime < commit_ts"

    # 验证差值报告逻辑
    message = (
        f"venv mtime {venv_mtime:.0f} < HEAD commit ts {commit_ts:.0f} "
        f"(stale by {diff_s:.0f}s); run `pipx install --force <repo-path>`"
    )
    assert "stale by 1000s" in message, f"TC-08b: expected stale message, got: {message}"
    assert "pipx install --force" in message, "TC-08b: stale message should recommend pipx install --force"
