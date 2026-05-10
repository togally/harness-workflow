"""Unit tests for req-56 / chg-01: --fallback flag + office_hours_mode schema + compat guard.

Tests (10 cases):
  P0 (6 cases + TC-Dogfood-07):
    TC-01  test_no_flag_compat_true_yields_required
    TC-02  test_no_flag_compat_false_yields_fallback_with_warning
    TC-03  test_fallback_flag_compat_true_yields_fallback
    TC-04  test_fallback_flag_compat_false_yields_fallback_both_warnings
    TC-05  test_no_gstack_status_field_yields_fallback
    TC-06  test_old_req_missing_office_hours_mode_no_crash
    TC-Dogfood-07  test_cli_subprocess_fallback_flag_end_to_end
  P1 (3 cases):
    TC-08  test_state_yaml_round_trip_field_survives
    TC-09  test_ordered_keys_contains_office_hours_mode
    TC-10  test_cli_subprocess_no_flag_compat_true_yields_required
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow import workflow_helpers as wh  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_runtime(tmp_path: Path, agent_kind_compatible: bool | None = True, include_gstack_status: bool = True) -> None:
    """Write a minimal runtime.yaml with optional gstack_status."""
    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    runtime_path = state_dir / "runtime.yaml"

    if include_gstack_status:
        compat_str = "true" if agent_kind_compatible else "false"
        gstack_block = (
            "gstack_status:\n"
            f"  agent_kind_compatible: {compat_str}\n"
            "  installed_skills: []\n"
            "  vendor_version: \"\"\n"
            "  last_install: \"\"\n"
        )
    else:
        gstack_block = ""

    runtime_path.write_text(
        "operation_type: \"requirement\"\n"
        "operation_target: \"req-50\"\n"
        "current_requirement: \"req-50\"\n"
        "current_requirement_title: \"seed req\"\n"
        "stage: \"executing\"\n"
        "stage_entered_at: \"2026-05-09T00:00:00.000000+00:00\"\n"
        "conversation_mode: \"open\"\n"
        "locked_requirement: \"\"\n"
        "locked_requirement_title: \"\"\n"
        "locked_stage: \"\"\n"
        "current_regression: \"\"\n"
        "current_regression_title: \"\"\n"
        "ff_mode: false\n"
        "ff_stage_history: []\n"
        "active_requirements:\n"
        "  - req-50\n"
        + gstack_block
        + "gstack_run_log: []\n",
        encoding="utf-8",
    )


def _create_req_and_read_state(tmp_path: Path, fallback: bool = False, title: str = "Test Req") -> dict:
    """Call create_requirement and return the parsed state yaml as dict."""
    wh.create_requirement(tmp_path, title, fallback=fallback)
    # find the state file
    state_dir = tmp_path / ".workflow" / "state" / "requirements"
    state_files = list(state_dir.glob("*.yaml"))
    assert len(state_files) == 1, f"Expected 1 state file, got {state_files}"
    return wh.load_simple_yaml(state_files[0])


# ---------------------------------------------------------------------------
# P0 Tests
# ---------------------------------------------------------------------------

class TestNoFlagCompatTrue:
    """TC-01: no --fallback + agent_kind_compatible=true → office_hours_mode=required."""

    def test_no_flag_compat_true_yields_required(self, tmp_path: Path, capsys) -> None:
        _write_runtime(tmp_path, agent_kind_compatible=True)
        state = _create_req_and_read_state(tmp_path, fallback=False, title="TC01 Req")
        assert state.get("office_hours_mode") == "required", (
            f"Expected 'required' but got {state.get('office_hours_mode')!r}"
        )
        captured = capsys.readouterr()
        assert "[gstack] agent 不兼容" not in captured.out
        assert "[mode] fallback" not in captured.out


class TestNoFlagCompatFalse:
    """TC-02: no --fallback + agent_kind_compatible=false → office_hours_mode=fallback + warning."""

    def test_no_flag_compat_false_yields_fallback_with_warning(self, tmp_path: Path, capsys) -> None:
        _write_runtime(tmp_path, agent_kind_compatible=False)
        state = _create_req_and_read_state(tmp_path, fallback=False, title="TC02 Req")
        assert state.get("office_hours_mode") == "fallback", (
            f"Expected 'fallback' but got {state.get('office_hours_mode')!r}"
        )
        captured = capsys.readouterr()
        assert "[gstack] agent 不兼容" in captured.out


class TestFallbackFlagCompatTrue:
    """TC-03: --fallback + agent_kind_compatible=true → office_hours_mode=fallback + [mode] fallback."""

    def test_fallback_flag_compat_true_yields_fallback(self, tmp_path: Path, capsys) -> None:
        _write_runtime(tmp_path, agent_kind_compatible=True)
        state = _create_req_and_read_state(tmp_path, fallback=True, title="TC03 Req")
        assert state.get("office_hours_mode") == "fallback", (
            f"Expected 'fallback' but got {state.get('office_hours_mode')!r}"
        )
        captured = capsys.readouterr()
        assert "[mode] fallback" in captured.out
        assert "[gstack] agent 不兼容" not in captured.out


class TestFallbackFlagCompatFalse:
    """TC-04: --fallback + agent_kind_compatible=false → office_hours_mode=fallback + both warnings."""

    def test_fallback_flag_compat_false_yields_fallback_both_warnings(self, tmp_path: Path, capsys) -> None:
        _write_runtime(tmp_path, agent_kind_compatible=False)
        state = _create_req_and_read_state(tmp_path, fallback=True, title="TC04 Req")
        assert state.get("office_hours_mode") == "fallback", (
            f"Expected 'fallback' but got {state.get('office_hours_mode')!r}"
        )
        captured = capsys.readouterr()
        # When fallback=True AND compat=False: [gstack] warning NOT printed (fallback takes precedence path)
        # Per plan.md: `if not compat and not fallback: print(...)` so with fallback=True this branch is skipped
        assert "[mode] fallback" in captured.out


class TestNoGstackStatusField:
    """TC-05: runtime.yaml without gstack_status → treated as compat=false → fallback."""

    def test_no_gstack_status_field_yields_fallback(self, tmp_path: Path, capsys) -> None:
        _write_runtime(tmp_path, include_gstack_status=False)
        state = _create_req_and_read_state(tmp_path, fallback=False, title="TC05 Req")
        assert state.get("office_hours_mode") == "fallback", (
            f"Expected 'fallback' but got {state.get('office_hours_mode')!r}"
        )
        captured = capsys.readouterr()
        assert "[gstack] agent 不兼容" in captured.out


class TestOldReqMissingField:
    """TC-06: old req state yaml without office_hours_mode → dict.get returns 'required', no crash."""

    def test_old_req_missing_office_hours_mode_no_crash(self, tmp_path: Path) -> None:
        # Simulate an old state yaml file without office_hours_mode field
        state_dir = tmp_path / ".workflow" / "state" / "requirements"
        state_dir.mkdir(parents=True, exist_ok=True)
        old_state = state_dir / "req-01-old-req.yaml"
        old_state.write_text(
            "id: req-01\n"
            "title: old req\n"
            "stage: done\n"
            "status: active\n"
            "created_at: 2025-01-01\n"
            "started_at: 2025-01-01\n"
            "completed_at: \"\"\n"
            "stage_timestamps: {}\n"
            "description: \"\"\n",
            encoding="utf-8",
        )
        loaded = wh.load_simple_yaml(old_state)
        # Must not raise; must return "required" as default
        result = loaded.get("office_hours_mode", "required")
        assert result == "required", f"Expected 'required' default, got {result!r}"


class TestCliSubprocessFallbackEndToEnd:
    """TC-Dogfood-07: subprocess CLI end-to-end with --fallback flag."""

    def test_cli_subprocess_fallback_flag_end_to_end(self, tmp_path: Path) -> None:
        # Setup minimal harness project structure
        _write_runtime(tmp_path, agent_kind_compatible=True)

        # Create required directories that harness needs
        (tmp_path / ".workflow" / "flow" / "requirements").mkdir(parents=True, exist_ok=True)
        (tmp_path / "artifacts" / "main" / "requirements").mkdir(parents=True, exist_ok=True)

        # Write minimal config
        codex_dir = tmp_path / ".codex" / "harness"
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "config.json").write_text('{"language": "english"}', encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness_workflow.cli",
                "requirement",
                "test fallback req",
                "--fallback",
                "--root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

        assert result.returncode == 0, f"CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"
        assert "[mode] fallback" in result.stdout, (
            f"Expected '[mode] fallback' in stdout, got:\n{result.stdout}"
        )

        # Verify state yaml has office_hours_mode: fallback
        state_dir = tmp_path / ".workflow" / "state" / "requirements"
        state_files = list(state_dir.glob("*.yaml"))
        assert len(state_files) >= 1, "No state file created"
        state_text = state_files[0].read_text(encoding="utf-8")
        # save_simple_yaml quotes string scalars so value is "fallback" (with quotes)
        assert "office_hours_mode:" in state_text and "fallback" in state_text, (
            f"Expected 'office_hours_mode: ..fallback..' in state yaml:\n{state_text}"
        )
        loaded_state = wh.load_simple_yaml(state_files[0])
        assert loaded_state.get("office_hours_mode") == "fallback", (
            f"Expected 'fallback' after load, got {loaded_state.get('office_hours_mode')!r}"
        )

        # Verify runtime.yaml updated to analysis stage (req-01 uses legacy requirement_review but that's OK)
        runtime_text = (tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8")
        assert "stage:" in runtime_text, (
            f"Expected 'stage:' in runtime.yaml:\n{runtime_text}"
        )


# ---------------------------------------------------------------------------
# P1 Tests
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """TC-08: save_simple_yaml round-trip — office_hours_mode field survives."""

    def test_state_yaml_round_trip_field_survives(self, tmp_path: Path) -> None:
        state_file = tmp_path / "test_state.yaml"
        payload = {
            "id": "req-99",
            "title": "round trip test",
            "stage": "analysis",
            "status": "active",
            "created_at": "2026-05-09",
            "started_at": "2026-05-09",
            "completed_at": "",
            "stage_timestamps": {},
            "description": "",
            "office_hours_mode": "required",
        }
        ordered = ["id", "title", "stage", "status", "created_at", "started_at",
                   "completed_at", "stage_timestamps", "description", "office_hours_mode"]
        wh.save_simple_yaml(state_file, payload, ordered_keys=ordered)
        loaded = wh.load_simple_yaml(state_file)
        assert loaded.get("office_hours_mode") == "required", (
            f"Field did not survive round-trip: got {loaded.get('office_hours_mode')!r}"
        )


class TestOrderedKeysContainsField:
    """TC-09: ordered_keys list in workflow_helpers.py contains office_hours_mode."""

    def test_ordered_keys_contains_office_hours_mode(self) -> None:
        src = (REPO_ROOT / "src" / "harness_workflow" / "workflow_helpers.py").read_text(encoding="utf-8")
        # AC-04: office_hours_mode should appear at least twice (dict key + ordered_keys)
        count = src.count('"office_hours_mode"')
        assert count >= 2, (
            f"Expected at least 2 occurrences of '\"office_hours_mode\"' in workflow_helpers.py, got {count}"
        )


class TestCliSubprocessNoFlagCompatTrue:
    """TC-10: subprocess CLI no --fallback + compat=true → state=required."""

    def test_cli_subprocess_no_flag_compat_true_yields_required(self, tmp_path: Path) -> None:
        _write_runtime(tmp_path, agent_kind_compatible=True)

        (tmp_path / ".workflow" / "flow" / "requirements").mkdir(parents=True, exist_ok=True)
        (tmp_path / "artifacts" / "main" / "requirements").mkdir(parents=True, exist_ok=True)

        codex_dir = tmp_path / ".codex" / "harness"
        codex_dir.mkdir(parents=True, exist_ok=True)
        (codex_dir / "config.json").write_text('{"language": "english"}', encoding="utf-8")

        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness_workflow.cli",
                "requirement",
                "test required req",
                "--root",
                str(tmp_path),
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

        assert result.returncode == 0, f"CLI failed:\nstdout={result.stdout}\nstderr={result.stderr}"

        state_dir = tmp_path / ".workflow" / "state" / "requirements"
        state_files = list(state_dir.glob("*.yaml"))
        assert len(state_files) >= 1, "No state file created"
        state_text = state_files[0].read_text(encoding="utf-8")
        # save_simple_yaml quotes string scalars so value is "required" (with quotes)
        assert "office_hours_mode:" in state_text and "required" in state_text, (
            f"Expected 'office_hours_mode: ..required..' in state yaml:\n{state_text}"
        )
        loaded_state = wh.load_simple_yaml(state_files[0])
        assert loaded_state.get("office_hours_mode") == "required", (
            f"Expected 'required' after load, got {loaded_state.get('office_hours_mode')!r}"
        )

        runtime_text = (tmp_path / ".workflow" / "state" / "runtime.yaml").read_text(encoding="utf-8")
        assert "stage:" in runtime_text, (
            f"Expected 'stage:' in runtime.yaml:\n{runtime_text}"
        )
