"""Unit tests for fix-checklist files + lint output改造.

req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
/ chg-02（fix-checklist 首批 3 个 + lint 输出加指针）

13 TC covering:
  - 3 fix-checklist files existence + 5-section structure
  - check_artifact_placement verbose flag + raise_harness_block
  - check_schema_audit FAIL / PASS
  - check_missing_document FAIL / PASS
  - CLI routing for schema-audit + missing-document
  - mirror sync for 3 fix-checklist files
  - unknown contract → exit ≠ 0
  - TC-Dogfood-13 end-to-end artifact-placement
"""
from __future__ import annotations

import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
CHECKLISTS_DIR = ROOT / ".workflow" / "context" / "checklists"

_REQUIRED_SECTIONS = (
    "## 触发条件",
    "## 修复步骤",
    "## 验证步骤",
    "## 回退路径",
    "## dogfood 样本",
)


# ---------------------------------------------------------------------------
# TC-01: 3 fix-checklist files exist with 5 sections
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", [
    "fix-artifact-placement.md",
    "fix-schema-audit.md",
    "fix-missing-document.md",
])
def test_tc01_checklist_files_exist_with_sections(fname):
    """TC-01: Each fix-checklist exists and has all 5 required sections."""
    path = CHECKLISTS_DIR / fname
    assert path.exists(), f"{fname} not found at {path}"
    content = path.read_text(encoding="utf-8")
    for section in _REQUIRED_SECTIONS:
        assert section in content, f"{fname} missing section: {section!r}"


# ---------------------------------------------------------------------------
# TC-02: artifact-placement FAIL triggers HARNESS_BLOCK
# ---------------------------------------------------------------------------

def test_tc02_artifact_placement_fail_block(tmp_path):
    """TC-02: check_artifact_placement(verbose=True) on violation → rc=64, HARNESS_BLOCK."""
    from harness_workflow.validate_contract import check_artifact_placement
    import io, contextlib

    # create violation: artifacts/main/requirements/req-99-x/planning/session-memory.md
    viol = tmp_path / "artifacts" / "main" / "requirements" / "req-99-x" / "planning" / "session-memory.md"
    viol.parent.mkdir(parents=True)
    viol.write_text("session content", encoding="utf-8")

    buf = io.StringIO()
    import contextlib
    with contextlib.redirect_stdout(buf):
        rc = check_artifact_placement(tmp_path, verbose=True)

    output = buf.getvalue()
    # rc should be 64 (HARNESS_BLOCK FAIL) or 1 (ImportError fallback)
    assert rc in (64, 1), f"expected 64 or 1, got {rc}"
    assert "FAIL" in output or "FAIL" in output

    # Check runtime-block.yaml exists when rc=64
    if rc == 64:
        block_yaml = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
        assert block_yaml.exists(), "runtime-block.yaml not created"
        import yaml as _yaml
        data = _yaml.safe_load(block_yaml.read_text()) or {}
        assert data.get("error_type") == "artifact-placement"
        assert data.get("severity") == "FAIL"


# ---------------------------------------------------------------------------
# TC-03: artifact-placement PASS + verbose=True
# ---------------------------------------------------------------------------

def test_tc03_artifact_placement_pass_verbose_true(tmp_path, capsys):
    """TC-03: clean dir → check_artifact_placement(verbose=True) → rc=0, PASS in stdout."""
    from harness_workflow.validate_contract import check_artifact_placement
    rc = check_artifact_placement(tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert rc == 0, f"expected 0, got {rc}"
    assert "PASS" in captured.out


# ---------------------------------------------------------------------------
# TC-04: artifact-placement PASS + verbose=False
# ---------------------------------------------------------------------------

def test_tc04_artifact_placement_pass_verbose_false(tmp_path, capsys):
    """TC-04: clean dir → check_artifact_placement(verbose=False) → rc=0, no PASS in stdout."""
    from harness_workflow.validate_contract import check_artifact_placement
    rc = check_artifact_placement(tmp_path, verbose=False)
    captured = capsys.readouterr()
    assert rc == 0, f"expected 0, got {rc}"
    # verbose=False → PASS line should NOT appear
    assert "PASS" not in captured.out, f"Expected no PASS in stdout, got: {captured.out!r}"


# ---------------------------------------------------------------------------
# TC-05: schema-audit FAIL
# ---------------------------------------------------------------------------

def test_tc05_schema_audit_fail(tmp_path, capsys):
    """TC-05: old req-XX dir in state/requirements/ → HARNESS_BLOCK: schema-audit."""
    from harness_workflow.validate_contract import check_schema_audit

    # Create old-style dir: .workflow/state/requirements/req-99/
    old_dir = tmp_path / ".workflow" / "state" / "requirements" / "req-99"
    old_dir.mkdir(parents=True)

    rc = check_schema_audit(tmp_path, verbose=True)
    captured = capsys.readouterr()

    assert rc in (64, 1), f"expected 64 or 1, got {rc}"
    assert "HARNESS_BLOCK: schema-audit" in captured.out or "FAIL: schema-audit" in captured.out
    # fix-checklist pointer must appear
    assert "fix-schema-audit.md" in captured.out


# ---------------------------------------------------------------------------
# TC-06: schema-audit PASS
# ---------------------------------------------------------------------------

def test_tc06_schema_audit_pass(tmp_path, capsys):
    """TC-06: no old dirs → schema-audit PASS."""
    from harness_workflow.validate_contract import check_schema_audit

    # Create a properly named yaml file (not a directory)
    req_state = tmp_path / ".workflow" / "state" / "requirements"
    req_state.mkdir(parents=True)
    (req_state / "req-99-my-req.yaml").write_text("status: active\n", encoding="utf-8")

    rc = check_schema_audit(tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert rc == 0, f"expected 0, got {rc}"
    assert "PASS" in captured.out


# ---------------------------------------------------------------------------
# TC-07: missing-document FAIL (planning stage, changes/ empty)
# ---------------------------------------------------------------------------

def test_tc07_missing_document_fail(tmp_path, capsys):
    """TC-07: planning stage with empty changes/ → HARNESS_BLOCK: missing-document."""
    from harness_workflow.validate_contract import check_missing_document

    # Set up runtime.yaml
    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "runtime.yaml").write_text(
        'stage: "planning"\ncurrent_requirement: "req-99"\noperation_type: "requirement"\n',
        encoding="utf-8"
    )
    # Create req dir with requirement.md but empty changes/
    req_dir = tmp_path / ".workflow" / "flow" / "requirements" / "req-99-my-req"
    req_dir.mkdir(parents=True)
    (req_dir / "requirement.md").write_text("# req-99\n", encoding="utf-8")
    changes_dir = req_dir / "changes"
    changes_dir.mkdir()

    rc = check_missing_document(tmp_path, verbose=True)
    captured = capsys.readouterr()

    assert rc in (64, 1), f"expected 64 or 1, got {rc}"
    assert "FAIL: missing-document" in captured.out
    assert "fix-missing-document.md" in captured.out

    # retry_context should contain 'missing'
    if rc == 64:
        import yaml as _yaml
        block = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
        data = _yaml.safe_load(block.read_text()) or {}
        assert "missing" in str(data.get("retry_context", {}))


# ---------------------------------------------------------------------------
# TC-08: missing-document PASS
# ---------------------------------------------------------------------------

def test_tc08_missing_document_pass(tmp_path, capsys):
    """TC-08: planning stage with complete chg dirs → PASS."""
    from harness_workflow.validate_contract import check_missing_document

    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "runtime.yaml").write_text(
        'stage: "planning"\ncurrent_requirement: "req-99"\noperation_type: "requirement"\n',
        encoding="utf-8"
    )
    req_dir = tmp_path / ".workflow" / "flow" / "requirements" / "req-99-slug"
    req_dir.mkdir(parents=True)
    (req_dir / "requirement.md").write_text("# req-99\n", encoding="utf-8")

    chg_dir = req_dir / "changes" / "chg-01-my-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "change.md").write_text("# change\n", encoding="utf-8")
    (chg_dir / "plan.md").write_text("# plan\n", encoding="utf-8")

    rc = check_missing_document(tmp_path, verbose=True)
    captured = capsys.readouterr()
    assert rc == 0, f"expected 0, got {rc}"
    assert "PASS" in captured.out


# ---------------------------------------------------------------------------
# TC-09: CLI schema-audit runs without error on clean dir
# ---------------------------------------------------------------------------

def test_tc09_cli_schema_audit(tmp_path):
    """TC-09: CLI schema-audit on clean tmpdir → exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "schema-audit"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert "unknown contract" not in result.stderr


# ---------------------------------------------------------------------------
# TC-10: CLI missing-document on clean dir → exit 0
# ---------------------------------------------------------------------------

def test_tc10_cli_missing_document(tmp_path):
    """TC-10: CLI missing-document on dir with no runtime.yaml → exit 0 (skipped)."""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "missing-document"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode == 0, f"exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    assert "unknown contract" not in result.stderr


# ---------------------------------------------------------------------------
# TC-11: mirror sync for 3 fix-checklist files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fname", [
    "fix-artifact-placement.md",
    "fix-schema-audit.md",
    "fix-missing-document.md",
])
def test_tc11_mirror_checklists(fname):
    """TC-11: fix-checklist mirror is identical to live."""
    live = ROOT / ".workflow" / "context" / "checklists" / fname
    mirror = ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "checklists" / fname
    assert live.exists() and mirror.exists(), f"File missing: {fname}"
    assert live.read_bytes() == mirror.read_bytes(), f"Mirror drift: {fname}"


# ---------------------------------------------------------------------------
# TC-12: unknown contract → exit ≠ 0 + stderr mentions "unknown contract"
# ---------------------------------------------------------------------------

def test_tc12_unknown_contract(tmp_path):
    """TC-12: unknown contract name → exit ≠ 0 + error message in output."""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "bogus-name"],
        cwd=tmp_path, capture_output=True, text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")},
    )
    assert result.returncode != 0, f"expected non-zero, got {result.returncode}"
    # argparse rejects unknown choices with "invalid choice" or run_contract_cli prints "unknown contract"
    combined = result.stderr.lower() + result.stdout.lower()
    assert "invalid choice" in combined or "unknown contract" in combined, \
        f"Expected error about invalid contract in output\nstdout={result.stdout}\nstderr={result.stderr}"


# ---------------------------------------------------------------------------
# TC-Dogfood-13: end-to-end artifact-placement via subprocess
# ---------------------------------------------------------------------------

def test_tc_dogfood_13_e2e_artifact_placement(tmp_path):
    """TC-Dogfood-13: construct violation → subprocess validate → assert exit=64 + HARNESS_BLOCK + runtime-block.yaml."""
    import os

    # Build minimal .workflow structure in tmpdir
    (tmp_path / ".workflow" / "state").mkdir(parents=True)
    (tmp_path / ".workflow" / "context").mkdir(parents=True)
    # Construct violation: session-memory.md in artifacts/
    viol = tmp_path / "artifacts" / "main" / "requirements" / "req-99-x" / "planning" / "session-memory.md"
    viol.parent.mkdir(parents=True)
    viol.write_text("session content", encoding="utf-8")

    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", "artifact-placement"],
        cwd=tmp_path, capture_output=True, text=True, env=env,
    )

    assert result.returncode == 64, (
        f"Expected exit 64, got {result.returncode}\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    combined = result.stdout + result.stderr
    assert "HARNESS_BLOCK: artifact-placement" in combined, \
        f"HARNESS_BLOCK not in output: {combined!r}"
    assert "fix-checklist: .workflow/context/checklists/fix-artifact-placement.md" in combined, \
        f"fix-checklist pointer missing: {combined!r}"

    # runtime-block.yaml should be written by subprocess
    block_path = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    assert block_path.exists(), "runtime-block.yaml not created"
    import yaml as _yaml
    data = _yaml.safe_load(block_path.read_text()) or {}
    assert data.get("error_type") == "artifact-placement", f"error_type wrong: {data}"
    assert data.get("severity") == "FAIL", f"severity wrong: {data}"
    assert data.get("recovery_attempts") == 1, f"recovery_attempts wrong: {data}"
