"""Tests for bugfix-12: harness archive 输入未识别时误归档首个 done req (sug-74 同型病活证强化).

Tests (10 cases, all P0):
  TC-01  test_archive_nonexistent_req_id_exits_1_with_error
  TC-02  test_archive_nonexistent_bugfix_id_exits_1_with_error
  TC-03  test_archive_valid_bugfix_id_archives_correct_req
  TC-04  test_archive_valid_req_id_archives_correct_req
  TC-05  test_archive_no_arg_runtime_not_in_done_exits_1
  TC-06  test_archive_no_arg_runtime_in_done_archives_current
  TC-Dogfood-07  test_archive_nonexistent_id_no_file_movement
  TC-08  test_prompt_selection_preselect_not_in_reqs_returns_none
  TC-09  test_prompt_selection_preselect_in_reqs_returns_preselect
  TC-10  test_prompt_selection_no_preselect_returns_first
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _write_runtime(tmp_path: Path, current_requirement: str = "req-50") -> None:
    """Write a minimal runtime.yaml."""
    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "runtime.yaml").write_text(
        f'operation_type: "requirement"\n'
        f'operation_target: "{current_requirement}"\n'
        f'current_requirement: "{current_requirement}"\n'
        f'current_requirement_title: "test req"\n'
        f'stage: "done"\n'
        f'stage_entered_at: "2026-05-10T00:00:00.000000+00:00"\n'
        f'conversation_mode: "open"\n'
        f'locked_requirement: ""\n'
        f'locked_requirement_title: ""\n'
        f'locked_stage: ""\n'
        f'current_regression: ""\n'
        f'current_regression_title: ""\n'
        f'ff_mode: false\n'
        f'ff_stage_history: []\n'
        f'active_requirements:\n'
        f'  - "{current_requirement}"\n'
        f'gstack_run_log: []\n',
        encoding="utf-8",
    )


def _write_done_req_state(
    tmp_path: Path,
    req_id: str,
    title: str = "test req",
    kind: str = "requirements",
) -> None:
    """Write a done req/bugfix state yaml."""
    state_dir = tmp_path / ".workflow" / "state" / kind
    state_dir.mkdir(parents=True, exist_ok=True)
    slug = req_id.replace("-", "-")
    fname = f"{req_id}-{title.replace(' ', '-')}.yaml"
    (state_dir / fname).write_text(
        f'id: "{req_id}"\n'
        f'title: "{title}"\n'
        f'stage: "done"\n'
        f'status: "active"\n'
        f'created_at: "2026-05-01"\n'
        f'started_at: "2026-05-01"\n'
        f'completed_at: "2026-05-10"\n'
        f'description: ""\n',
        encoding="utf-8",
    )


def _setup_minimal_project(tmp_path: Path) -> None:
    """Set up the minimal directory structure needed by the CLI."""
    # Required directories
    for d in [
        ".workflow/state/requirements",
        ".workflow/state/bugfixes",
        ".workflow/flow/requirements",
        ".workflow/flow/bugfixes",
        ".workflow/flow/archive",
        "artifacts/main/requirements",
    ]:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Minimal config
    codex_dir = tmp_path / ".codex" / "harness"
    codex_dir.mkdir(parents=True, exist_ok=True)
    (codex_dir / "config.json").write_text(
        json.dumps({"language": "english"}, ensure_ascii=False),
        encoding="utf-8",
    )


def _run_archive_cli(tmp_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run harness archive CLI as subprocess in tmp_path."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

    cmd = [
        sys.executable,
        "-m",
        "harness_workflow.cli",
        "archive",
        "--root",
        str(tmp_path),
        *extra_args,
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )


def _get_state_dir_snapshot(tmp_path: Path) -> set[str]:
    """Return set of all files under .workflow/state/ to detect mutations."""
    state_dir = tmp_path / ".workflow" / "state"
    if not state_dir.exists():
        return set()
    return {str(p.relative_to(state_dir)) for p in state_dir.rglob("*") if p.is_file()}


def _get_flow_dir_snapshot(tmp_path: Path) -> set[str]:
    """Return set of all files under .workflow/flow/ to detect mutations."""
    flow_dir = tmp_path / ".workflow" / "flow"
    if not flow_dir.exists():
        return set()
    return {str(p.relative_to(flow_dir)) for p in flow_dir.rglob("*") if p.is_file()}


# ---------------------------------------------------------------------------
# TC-01: non-tty harness archive <nonexistent req-id> → exit 1 + error in stderr
# ---------------------------------------------------------------------------

class TestTC01NonexistentReqIdExits1:
    """TC-01: non-tty `harness archive req-99` (req-99 不存在) → exit 1 + stderr 含错误提示."""

    def test_archive_nonexistent_req_id_exits_1_with_error(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-50")
        # Only req-53 is done, req-99 does not exist
        _write_done_req_state(tmp_path, "req-53", "existing done req", kind="requirements")

        result = _run_archive_cli(tmp_path, "req-99")

        assert result.returncode == 1, (
            f"Expected exit 1 for nonexistent id, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "不在 done 列表中" in result.stderr, (
            f"Expected '不在 done 列表中' in stderr, got:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# TC-02: non-tty harness archive <nonexistent bugfix-id> → exit 1 + error
# ---------------------------------------------------------------------------

class TestTC02NonexistentBugfixIdExits1:
    """TC-02: non-tty `harness archive bugfix-99` (bugfix-99 不存在) → exit 1 + stderr 含错误提示."""

    def test_archive_nonexistent_bugfix_id_exits_1_with_error(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-53")
        _write_done_req_state(tmp_path, "req-53", "existing done req", kind="requirements")

        result = _run_archive_cli(tmp_path, "bugfix-99")

        assert result.returncode == 1, (
            f"Expected exit 1 for nonexistent bugfix id, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "不在 done 列表中" in result.stderr, (
            f"Expected '不在 done 列表中' in stderr, got:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# TC-03: non-tty harness archive bugfix-11 (in done_reqs) → archives bugfix-11
# ---------------------------------------------------------------------------

class TestTC03ValidBugfixIdArchivesCorrect:
    """TC-03: non-tty `harness archive bugfix-11` (stage=done) → exit 0 + 归档 bugfix-11."""

    def test_archive_valid_bugfix_id_archives_correct_req(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-50")

        # Setup req-53 (done) and bugfix-11 (done); req-53 is done_reqs[0]
        _write_done_req_state(tmp_path, "req-53", "first done req", kind="requirements")
        _write_done_req_state(tmp_path, "bugfix-11", "the bugfix", kind="bugfixes")

        # Setup minimal flow dirs for bugfix-11
        bf_flow_dir = tmp_path / ".workflow" / "flow" / "bugfixes" / "bugfix-11-the-bugfix"
        bf_flow_dir.mkdir(parents=True, exist_ok=True)
        (bf_flow_dir / "bugfix.md").write_text("# Bugfix\n", encoding="utf-8")

        result = _run_archive_cli(tmp_path, "bugfix-11", "--skip-revert-check")

        assert result.returncode == 0, (
            f"Expected exit 0 for valid bugfix-11 id, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        # Confirm bugfix-11 was archived (not req-53)
        assert "bugfix-11" in result.stdout, (
            f"Expected 'bugfix-11' in stdout, got:\n{result.stdout}"
        )
        # Confirm req-53 was NOT archived
        assert "req-53" not in result.stdout or "bugfix-11" in result.stdout, (
            f"req-53 should not be mentioned as archived:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# TC-04: non-tty harness archive req-53 (in done_reqs) → archives req-53
# ---------------------------------------------------------------------------

class TestTC04ValidReqIdArchivesCorrect:
    """TC-04: non-tty `harness archive req-53` (stage=done) → exit 0 + 归档 req-53."""

    def test_archive_valid_req_id_archives_correct_req(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-53")

        _write_done_req_state(tmp_path, "req-53", "the req", kind="requirements")
        _write_done_req_state(tmp_path, "req-54", "second done req", kind="requirements")

        # Setup minimal flow dirs for req-53
        req_flow_dir = tmp_path / ".workflow" / "flow" / "requirements" / "req-53-the-req"
        req_flow_dir.mkdir(parents=True, exist_ok=True)
        (req_flow_dir / "requirement.md").write_text("# Req\n", encoding="utf-8")

        result = _run_archive_cli(tmp_path, "req-53", "--skip-revert-check")

        assert result.returncode == 0, (
            f"Expected exit 0 for valid req-53 id, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "req-53" in result.stdout, (
            f"Expected 'req-53' in stdout, got:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# TC-05: non-tty harness archive (no arg), runtime.current_requirement not in done_reqs → exit 1
# ---------------------------------------------------------------------------

class TestTC05NoArgRuntimeNotInDoneExits1:
    """TC-05: non-tty `harness archive` with runtime.current_requirement not in done_reqs → exit 1."""

    def test_archive_no_arg_runtime_not_in_done_exits_1(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        # current_requirement is req-57, but only req-53 is done
        _write_runtime(tmp_path, current_requirement="req-57")
        _write_done_req_state(tmp_path, "req-53", "first done req", kind="requirements")

        result = _run_archive_cli(tmp_path)  # no extra args

        assert result.returncode == 1, (
            f"Expected exit 1 when current_requirement not in done, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "不在 done 列表中" in result.stderr, (
            f"Expected '不在 done 列表中' in stderr, got:\n{result.stderr}"
        )


# ---------------------------------------------------------------------------
# TC-06: non-tty harness archive (no arg), runtime.current_requirement in done_reqs → exit 0
# ---------------------------------------------------------------------------

class TestTC06NoArgRuntimeInDoneArchivesCurrent:
    """TC-06: non-tty `harness archive` with runtime.current_requirement in done_reqs → exit 0."""

    def test_archive_no_arg_runtime_in_done_archives_current(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-53")
        _write_done_req_state(tmp_path, "req-53", "current done req", kind="requirements")
        _write_done_req_state(tmp_path, "req-54", "second done req", kind="requirements")

        # Setup minimal flow dirs for req-53
        req_flow_dir = tmp_path / ".workflow" / "flow" / "requirements" / "req-53-current-done-req"
        req_flow_dir.mkdir(parents=True, exist_ok=True)
        (req_flow_dir / "requirement.md").write_text("# Req\n", encoding="utf-8")

        result = _run_archive_cli(tmp_path, "--skip-revert-check")

        assert result.returncode == 0, (
            f"Expected exit 0 when current_requirement=req-53 in done, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "req-53" in result.stdout, (
            f"Expected 'req-53' in stdout, got:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# TC-Dogfood-07: non-tty harness archive req-99 → no file movement
# ---------------------------------------------------------------------------

class TestTCDogfood07NoFileMutation:
    """TC-Dogfood-07: subprocess `harness archive req-99` → exit 1 + .workflow state unchanged."""

    def test_archive_nonexistent_id_no_file_movement(self, tmp_path: Path) -> None:
        _setup_minimal_project(tmp_path)
        _write_runtime(tmp_path, current_requirement="req-53")
        _write_done_req_state(tmp_path, "req-53", "first done req", kind="requirements")

        # Snapshot before
        state_before = _get_state_dir_snapshot(tmp_path)
        flow_before = _get_flow_dir_snapshot(tmp_path)

        result = _run_archive_cli(tmp_path, "req-99")

        # Snapshot after
        state_after = _get_state_dir_snapshot(tmp_path)
        flow_after = _get_flow_dir_snapshot(tmp_path)

        assert result.returncode == 1, (
            f"Expected exit 1, got {result.returncode}.\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )
        assert "不在 done 列表中" in result.stderr, (
            f"Expected error in stderr, got:\n{result.stderr}"
        )
        # No file should have been moved or created
        assert state_before == state_after, (
            f"State dir was mutated!\nBefore: {state_before}\nAfter: {state_after}"
        )
        assert flow_before == flow_after, (
            f"Flow dir was mutated!\nBefore: {flow_before}\nAfter: {flow_after}"
        )


# ---------------------------------------------------------------------------
# TC-08: prompt_requirement_selection unit test: preselect not in reqs + non-tty → None
# ---------------------------------------------------------------------------

class TestTC08PromptSelectionPreselectedNotInReqs:
    """TC-08: prompt_requirement_selection unit test: preselect not in reqs + non-tty → None."""

    def test_prompt_selection_preselect_not_in_reqs_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from harness_workflow.cli import prompt_requirement_selection

        requirements = [
            {"req_id": "req-53", "title": "first", "stage": "done"},
            {"req_id": "req-54", "title": "second", "stage": "done"},
        ]

        # Simulate non-tty by patching sys.stdin.isatty
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        result = prompt_requirement_selection(requirements, preselect="req-99")

        assert result is None, (
            f"Expected None when preselect='req-99' not in requirements, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TC-09: prompt_requirement_selection unit test: preselect in reqs + non-tty → return preselect
# ---------------------------------------------------------------------------

class TestTC09PromptSelectionPreselectedInReqs:
    """TC-09: prompt_requirement_selection unit test: preselect in reqs + non-tty → return preselect."""

    def test_prompt_selection_preselect_in_reqs_returns_preselect(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from harness_workflow.cli import prompt_requirement_selection

        requirements = [
            {"req_id": "req-53", "title": "first", "stage": "done"},
            {"req_id": "req-54", "title": "second", "stage": "done"},
        ]

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        result = prompt_requirement_selection(requirements, preselect="req-54")

        assert result == "req-54", (
            f"Expected 'req-54' when preselect='req-54' in requirements, got {result!r}"
        )


# ---------------------------------------------------------------------------
# TC-10: prompt_requirement_selection unit test: preselect=None + non-tty → return requirements[0]
# ---------------------------------------------------------------------------

class TestTC10PromptSelectionNoPreselect:
    """TC-10: prompt_requirement_selection unit test: preselect=None + non-tty → requirements[0]."""

    def test_prompt_selection_no_preselect_returns_first(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from harness_workflow.cli import prompt_requirement_selection

        requirements = [
            {"req_id": "req-53", "title": "first", "stage": "done"},
            {"req_id": "req-54", "title": "second", "stage": "done"},
        ]

        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        result = prompt_requirement_selection(requirements, preselect=None)

        assert result == "req-53", (
            f"Expected 'req-53' (requirements[0]) when preselect=None, got {result!r}"
        )
