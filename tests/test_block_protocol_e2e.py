"""End-to-end dogfood tests for HARNESS_BLOCK block protocol.

req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
/ chg-03（reviewer 加项 + 端到端 dogfood + roadmap）

8 TC covering:
  - TC-01: review-checklist.md has 抛错协议配套 × 2 mentions
  - TC-02: reviewer.md references review-checklist.md
  - TC-Dogfood-03: artifact-placement closed loop: FAIL → fix → PASS
  - TC-Dogfood-04: schema-audit closed loop: FAIL → fix → PASS
  - TC-Dogfood-05: missing-document closed loop: FAIL → fix → PASS
  - TC-06: recovery_attempts accumulates across repeated calls
  - TC-07: review-checklist.md mirror is identical
  - TC-08: roadmap 骨架 in chg-03 plan.md
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


def _run_validate(contract: str, cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate", "--contract", contract],
        cwd=cwd, capture_output=True, text=True, env=env,
    )


def _read_block_yaml(tmp_path: Path) -> dict:
    block_path = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    if not block_path.exists():
        return {}
    return yaml.safe_load(block_path.read_text(encoding="utf-8")) or {}


# ---------------------------------------------------------------------------
# TC-01: review-checklist.md 加项存在 × 2
# ---------------------------------------------------------------------------

def test_tc01_review_checklist_entries():
    """TC-01: review-checklist.md has ≥2 occurrences of '抛错协议配套'."""
    path = ROOT / ".workflow" / "context" / "checklists" / "review-checklist.md"
    assert path.exists(), "review-checklist.md not found"
    content = path.read_text(encoding="utf-8")

    count = content.count("抛错协议配套")
    assert count >= 2, f"Expected ≥2 occurrences of '抛错协议配套', got {count}"
    assert "req-48" in content and "chg-03" in content, "req-48 / chg-03 references missing"


# ---------------------------------------------------------------------------
# TC-02: reviewer.md references review-checklist
# ---------------------------------------------------------------------------

def test_tc02_reviewer_md_reference():
    """TC-02: reviewer.md references review-checklist.md."""
    path = ROOT / ".workflow" / "context" / "roles" / "reviewer.md"
    assert path.exists(), "reviewer.md not found"
    content = path.read_text(encoding="utf-8")
    assert "review-checklist" in content.lower(), "reviewer.md missing review-checklist reference"


# ---------------------------------------------------------------------------
# TC-Dogfood-03: artifact-placement closed loop
# ---------------------------------------------------------------------------

def test_tc_dogfood_03_artifact_placement_loop(tmp_path):
    """TC-Dogfood-03: FAIL → fix (mv) → PASS closed loop for artifact-placement."""
    # Setup minimal .workflow/state
    (tmp_path / ".workflow" / "state").mkdir(parents=True)

    # Place violation: session-memory.md in artifacts/
    viol_src = tmp_path / "artifacts" / "main" / "requirements" / "req-99-x" / "planning" / "session-memory.md"
    viol_src.parent.mkdir(parents=True)
    viol_src.write_text("session content", encoding="utf-8")

    # Run 1: expect FAIL exit 64
    r1 = _run_validate("artifact-placement", tmp_path)
    assert r1.returncode == 64, (
        f"Expected 64, got {r1.returncode}\nstdout={r1.stdout!r}\nstderr={r1.stderr!r}"
    )
    combined1 = r1.stdout + r1.stderr
    assert "HARNESS_BLOCK: artifact-placement" in combined1
    assert "fix-checklist: .workflow/context/checklists/fix-artifact-placement.md" in combined1

    # Verify runtime-block.yaml
    data = _read_block_yaml(tmp_path)
    assert data.get("error_type") == "artifact-placement"
    assert data.get("severity") == "FAIL"
    assert data.get("recovery_attempts") == 1

    # Fix: simulate fix-artifact-placement.md instructions (mv to .workflow/flow/...)
    dest = tmp_path / ".workflow" / "flow" / "requirements" / "req-99-x" / "planning" / "session-memory.md"
    dest.parent.mkdir(parents=True)
    viol_src.rename(dest)
    # Remove empty parent dirs in artifacts/
    try:
        viol_src.parent.rmdir()
        viol_src.parent.parent.rmdir()
    except OSError:
        pass

    # Also clean up the runtime-block.yaml to simulate harness-manager clearing it
    block_path = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    block_path.write_text("{}\n", encoding="utf-8")

    # Run 2: expect PASS exit 0
    r2 = _run_validate("artifact-placement", tmp_path)
    assert r2.returncode == 0, (
        f"Expected 0 after fix, got {r2.returncode}\nstdout={r2.stdout!r}\nstderr={r2.stderr!r}"
    )
    assert "PASS" in r2.stdout


# ---------------------------------------------------------------------------
# TC-Dogfood-04: schema-audit closed loop
# ---------------------------------------------------------------------------

def test_tc_dogfood_04_schema_audit_loop(tmp_path):
    """TC-Dogfood-04: FAIL → fix (mv old dir) → PASS closed loop for schema-audit."""
    old_dir = tmp_path / ".workflow" / "state" / "requirements" / "req-99"
    old_dir.mkdir(parents=True)

    # Run 1: FAIL
    r1 = _run_validate("schema-audit", tmp_path)
    assert r1.returncode == 64, (
        f"Expected 64, got {r1.returncode}\nstdout={r1.stdout!r}\nstderr={r1.stderr!r}"
    )
    combined1 = r1.stdout + r1.stderr
    assert "HARNESS_BLOCK: schema-audit" in combined1
    assert "fix-schema-audit.md" in combined1

    # Fix: simulate fix-schema-audit.md instructions (archive the old dir)
    archive = tmp_path / ".workflow" / "state" / "requirements" / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    old_dir.rename(archive / "req-99")

    # Run 2: PASS
    r2 = _run_validate("schema-audit", tmp_path)
    assert r2.returncode == 0, (
        f"Expected 0, got {r2.returncode}\nstdout={r2.stdout!r}\nstderr={r2.stderr!r}"
    )
    assert "PASS" in r2.stdout


# ---------------------------------------------------------------------------
# TC-Dogfood-05: missing-document closed loop
# ---------------------------------------------------------------------------

def test_tc_dogfood_05_missing_document_loop(tmp_path):
    """TC-Dogfood-05: FAIL → fix (create missing files) → PASS closed loop for missing-document."""
    state_dir = tmp_path / ".workflow" / "state"
    state_dir.mkdir(parents=True)

    # planning stage with empty changes/ dir
    (state_dir / "runtime.yaml").write_text(
        'stage: "planning"\ncurrent_requirement: "req-99"\noperation_type: "requirement"\n',
        encoding="utf-8",
    )
    req_dir = tmp_path / ".workflow" / "flow" / "requirements" / "req-99-slug"
    req_dir.mkdir(parents=True)
    (req_dir / "requirement.md").write_text("# req-99\n", encoding="utf-8")
    (req_dir / "changes").mkdir()

    # Run 1: FAIL
    r1 = _run_validate("missing-document", tmp_path)
    assert r1.returncode == 64, (
        f"Expected 64, got {r1.returncode}\nstdout={r1.stdout!r}\nstderr={r1.stderr!r}"
    )
    combined1 = r1.stdout + r1.stderr
    assert "HARNESS_BLOCK: missing-document" in combined1
    assert "fix-missing-document.md" in combined1

    # Fix: create chg dir with change.md + plan.md
    chg_dir = req_dir / "changes" / "chg-01-my-change"
    chg_dir.mkdir(parents=True)
    (chg_dir / "change.md").write_text("# change\n", encoding="utf-8")
    (chg_dir / "plan.md").write_text("# plan\n## 4. 测试用例设计\n| TC | - |\n", encoding="utf-8")

    # Run 2: PASS
    r2 = _run_validate("missing-document", tmp_path)
    assert r2.returncode == 0, (
        f"Expected 0, got {r2.returncode}\nstdout={r2.stdout!r}\nstderr={r2.stderr!r}"
    )
    assert "PASS" in r2.stdout


# ---------------------------------------------------------------------------
# TC-06: recovery_attempts accumulates (no fix between runs)
# ---------------------------------------------------------------------------

def test_tc06_recovery_attempts_accumulate_via_cli(tmp_path):
    """TC-06: two consecutive FAIL runs without fix → recovery_attempts=2."""
    old_dir = tmp_path / ".workflow" / "state" / "requirements" / "req-77"
    old_dir.mkdir(parents=True)

    _run_validate("schema-audit", tmp_path)
    _run_validate("schema-audit", tmp_path)

    data = _read_block_yaml(tmp_path)
    # recovery_attempts should have incremented to 2
    assert data.get("recovery_attempts") == 2, f"expected 2, got {data.get('recovery_attempts')}"


# ---------------------------------------------------------------------------
# TC-07: mirror review-checklist.md
# ---------------------------------------------------------------------------

def test_tc07_mirror_review_checklist():
    """TC-07: review-checklist.md mirror is identical."""
    live = ROOT / ".workflow" / "context" / "checklists" / "review-checklist.md"
    mirror = (
        ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
        / ".workflow" / "context" / "checklists" / "review-checklist.md"
    )
    assert live.exists() and mirror.exists()
    assert live.read_bytes() == mirror.read_bytes(), "review-checklist.md mirror drift"


# ---------------------------------------------------------------------------
# TC-08: roadmap 骨架 in chg-03 plan.md
# ---------------------------------------------------------------------------

def test_tc08_roadmap_in_plan():
    """TC-08: chg-03 plan.md §5 has roadmap skeleton with 3 fix-checklists + 5 contracts."""
    plan_path = (
        ROOT / ".workflow" / "flow" / "requirements"
        / "req-48-harness-manager-统一异常捕获-base-role-阻塞抛错协议-fix-checklist-自动修复体系"
        / "changes" / "chg-03-reviewer加项-端到端dogfood-roadmap" / "plan.md"
    )
    assert plan_path.exists(), f"chg-03 plan.md not found: {plan_path}"
    content = plan_path.read_text(encoding="utf-8")

    # Should have roadmap section
    assert "留尾" in content or "roadmap" in content.lower(), "roadmap section missing"
    # Should reference 3 fix-checklist names
    expected_checklists = ["fix-user-write-protected-zones", "fix-build-cache-freshness", "fix-self-audit-drift"]
    for cl in expected_checklists:
        assert cl in content, f"roadmap missing fix-checklist: {cl}"
