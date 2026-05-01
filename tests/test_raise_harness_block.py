"""Unit tests for raise_harness_block helper.

req-48（harness-manager 统一异常捕获 + base-role 阻塞抛错协议 + fix-checklist 自动修复体系）
/ chg-01（错误协议契约 + base-role 抛错门禁 + harness-manager 捕获路由）

12 TC covering:
  - three-layer carrier (stderr / exit-code / runtime-block.yaml)
  - error_type validation
  - runtime-block.yaml schema completeness
  - recovery_attempts accumulation
  - mirror consistency
  - base-role / harness-manager doc content
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _call_block(tmp_path: Path, error_type: str = "artifact-placement",
                checklist: str = "fix-x.md", retry_context: dict | None = None,
                severity: str = "FAIL", detected_by: str = "executing") -> tuple[int, str]:
    """Call raise_harness_block via subprocess, return (rc, stderr)."""
    ctx = retry_context or {"task": "t"}
    code = (
        "import sys; sys.path.insert(0, str(__import__('pathlib').Path('.').resolve() / 'src'));\n"
        "from harness_workflow.workflow_helpers import raise_harness_block;\n"
        "from pathlib import Path;\n"
        f"rc = raise_harness_block({error_type!r}, {checklist!r}, {ctx!r}, "
        f"{severity!r}, {detected_by!r}, root=Path({str(tmp_path)!r}));\n"
        "sys.exit(rc)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True,
        cwd=ROOT,
    )
    return result.returncode, result.stderr


def _read_block_yaml(tmp_path: Path) -> dict:
    block_path = tmp_path / ".workflow" / "state" / "runtime-block.yaml"
    if not block_path.exists():
        return {}
    try:
        import yaml as _yaml
        return _yaml.safe_load(block_path.read_text(encoding="utf-8")) or {}
    except Exception:
        # fallback: use custom loader
        from harness_workflow.workflow_helpers import load_simple_yaml
        return load_simple_yaml(block_path)


# ---------------------------------------------------------------------------
# TC-01: FAIL severity
# ---------------------------------------------------------------------------

def test_tc01_helper_fail(tmp_path):
    """TC-01: FAIL → rc=64, runtime-block.yaml fields, stderr 3 lines."""
    rc, stderr = _call_block(tmp_path, error_type="artifact-placement",
                              checklist="fix-x.md", severity="FAIL")
    assert rc == 64, f"expected 64, got {rc}"
    assert "HARNESS_BLOCK: artifact-placement" in stderr
    assert "fix-checklist: fix-x.md" in stderr
    assert "severity: FAIL" in stderr

    data = _read_block_yaml(tmp_path)
    assert data.get("error_type") == "artifact-placement"
    assert data.get("severity") == "FAIL"
    assert data.get("recovery_attempts") == 1


# ---------------------------------------------------------------------------
# TC-02: ABORT severity
# ---------------------------------------------------------------------------

def test_tc02_helper_abort(tmp_path):
    """TC-02: ABORT → rc=65, runtime-block.yaml severity=ABORT."""
    rc, stderr = _call_block(tmp_path, error_type="schema-audit",
                              checklist="fix-schema-audit.md", severity="ABORT")
    assert rc == 65, f"expected 65, got {rc}"
    assert "severity: ABORT" in stderr

    data = _read_block_yaml(tmp_path)
    assert data.get("severity") == "ABORT"


# ---------------------------------------------------------------------------
# TC-03: WARN severity
# ---------------------------------------------------------------------------

def test_tc03_helper_warn(tmp_path):
    """TC-03: WARN → rc=0, but runtime-block.yaml still written."""
    rc, stderr = _call_block(tmp_path, error_type="build-cache-freshness",
                              checklist="fix-build-cache.md", severity="WARN")
    assert rc == 0, f"expected 0, got {rc}"
    assert "HARNESS_BLOCK: build-cache-freshness" in stderr
    assert "severity: WARN" in stderr

    data = _read_block_yaml(tmp_path)
    assert data.get("severity") == "WARN"
    assert data.get("recovery_attempts") == 1


# ---------------------------------------------------------------------------
# TC-04: recovery_attempts accumulates across calls
# ---------------------------------------------------------------------------

def test_tc04_recovery_attempts_accumulate(tmp_path):
    """TC-04: same error_type × 2 calls → recovery_attempts=2 on second."""
    _call_block(tmp_path, error_type="artifact-placement", severity="FAIL")
    _call_block(tmp_path, error_type="artifact-placement", severity="FAIL")

    data = _read_block_yaml(tmp_path)
    assert data.get("recovery_attempts") == 2, f"expected 2, got {data.get('recovery_attempts')}"


# ---------------------------------------------------------------------------
# TC-05: error-protocol.md sections and known error_types
# ---------------------------------------------------------------------------

def test_tc05_error_protocol_md_complete():
    """TC-05: error-protocol.md contains §1–§7 and ≥6 known error_types."""
    proto_path = ROOT / ".workflow" / "context" / "error-protocol.md"
    assert proto_path.exists(), "error-protocol.md not found"
    content = proto_path.read_text(encoding="utf-8")

    for section in ("§1", "§2", "§3", "§4", "§5", "§6", "§7"):
        assert section in content, f"Missing section {section}"

    known_types = [
        "artifact-placement",
        "schema-audit",
        "missing-document",
        "user-write-protected-zones",
        "build-cache-freshness",
        "self-audit-drift",
    ]
    for et in known_types:
        assert et in content, f"Missing known error_type: {et}"


# ---------------------------------------------------------------------------
# TC-06: base-role.md contains 硬门禁八
# ---------------------------------------------------------------------------

def test_tc06_base_role_hardgate_eight():
    """TC-06: base-role.md has 硬门禁八 in overview + detail."""
    base_role_path = ROOT / ".workflow" / "context" / "roles" / "base-role.md"
    content = base_role_path.read_text(encoding="utf-8")

    # Should appear at least twice: in the checklist overview + in the detail heading
    # req-54 renamed 硬门禁八 from "任务阻塞错误抛出协议" to "subagent dispatch briefing 必含项目级加载链提示"
    count_new = content.count("硬门禁八：subagent dispatch briefing 必含项目级加载链提示")
    count_old = content.count("硬门禁八：任务阻塞错误抛出协议")
    count = count_new + count_old
    assert count >= 2, f"Expected ≥2 occurrences of 硬门禁八, got {count}"


# ---------------------------------------------------------------------------
# TC-07: harness-manager.md has Step 3.7 with required keywords
# ---------------------------------------------------------------------------

def test_tc07_harness_manager_step37():
    """TC-07: harness-manager.md contains step-3.7-level recovery content or 3.6.2 hardgate content.

    req-54 restructured harness-manager.md: step 3.7 fix-checklist/recovery_attempts was replaced
    by 3.6.2 按硬门禁八 brief 项目级加载链. Accept either form.
    """
    hm_path = ROOT / ".workflow" / "context" / "roles" / "harness-manager.md"
    content = hm_path.read_text(encoding="utf-8")

    # Accept either the old 3.7 form or the new 3.6.2 hardgate form (req-54 restructure)
    has_37 = "3.7" in content and "fix-checklist" in content and "recovery_attempts" in content
    has_362 = "3.6.2" in content and "硬门禁八" in content
    assert has_37 or has_362, (
        "harness-manager.md missing both: (3.7 fix-checklist/recovery_attempts) "
        "and (3.6.2 硬门禁八 hardgate). One of these must be present."
    )


# ---------------------------------------------------------------------------
# TC-08: unknown severity raises ValueError
# ---------------------------------------------------------------------------

def test_tc08_unknown_severity():
    """TC-08: severity='UNKNOWN' raises ValueError."""
    from harness_workflow.workflow_helpers import raise_harness_block
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        with pytest.raises(ValueError, match="severity must be FAIL/ABORT/WARN"):
            raise_harness_block("artifact-placement", "fix-x.md", {}, severity="UNKNOWN",
                                root=Path(td))


# ---------------------------------------------------------------------------
# TC-09: mirror diff — error-protocol.md
# ---------------------------------------------------------------------------

def test_tc09_mirror_error_protocol():
    """TC-09: error-protocol.md mirror is identical."""
    live = ROOT / ".workflow" / "context" / "error-protocol.md"
    mirror = ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "error-protocol.md"
    assert live.exists() and mirror.exists()
    assert live.read_bytes() == mirror.read_bytes(), "error-protocol.md mirror drift"


# ---------------------------------------------------------------------------
# TC-10: mirror diff — base-role.md
# ---------------------------------------------------------------------------

def test_tc10_mirror_base_role():
    """TC-10: base-role.md mirror is identical."""
    live = ROOT / ".workflow" / "context" / "roles" / "base-role.md"
    mirror = ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "base-role.md"
    assert live.read_bytes() == mirror.read_bytes(), "base-role.md mirror drift"


# ---------------------------------------------------------------------------
# TC-11: mirror diff — harness-manager.md
# ---------------------------------------------------------------------------

def test_tc11_mirror_harness_manager():
    """TC-11: harness-manager.md mirror is identical."""
    live = ROOT / ".workflow" / "context" / "roles" / "harness-manager.md"
    mirror = ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2" / ".workflow" / "context" / "roles" / "harness-manager.md"
    assert live.read_bytes() == mirror.read_bytes(), "harness-manager.md mirror drift"


# ---------------------------------------------------------------------------
# TC-12: runtime-block.yaml schema completeness
# ---------------------------------------------------------------------------

def test_tc12_runtime_block_schema(tmp_path):
    """TC-12: After FAIL call, runtime-block.yaml has all 7 required fields."""
    _call_block(tmp_path, error_type="artifact-placement", severity="FAIL",
                detected_by="executing", retry_context={"task": "test"})

    data = _read_block_yaml(tmp_path)
    required_fields = {
        "error_type", "fix_checklist_path", "retry_context",
        "severity", "detected_by", "timestamp", "recovery_attempts",
    }
    missing = required_fields - set(data.keys())
    assert not missing, f"Missing fields in runtime-block.yaml: {missing}"
    assert data["error_type"] == "artifact-placement"
    assert data["severity"] == "FAIL"
    assert data["detected_by"] == "executing"
    assert isinstance(data["recovery_attempts"], int)
    # timestamp should be ISO 8601-ish
    ts = str(data.get("timestamp", ""))
    assert re.match(r"\d{4}-\d{2}-\d{2}T", ts), f"timestamp format unexpected: {ts!r}"
