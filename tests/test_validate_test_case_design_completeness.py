"""Tests for harness validate --contract test-case-design-completeness (bugfix-6 B5).

Tests:
- plan.md with §测试用例设计 → PASS
- plan.md without §测试用例设计 → FAIL
- plan.md with empty test cases → FAIL
- bugfix diagnosis.md with §测试用例设计 → PASS
- bugfix diagnosis.md without §测试用例设计 → FAIL
- CLI --contract test-case-design-completeness choice works
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from harness_workflow.validate_contract import check_test_case_design_completeness


# ─────────────────────── helper ────────────────────────


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


PLAN_WITH_DESIGN = """# Change Plan

## 1. Development Steps

...

## 4. 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/foo.py

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | foo input | expected result | AC-01 | P0 |
| TC-02 | edge case | error | AC-02 | P1 |
"""

PLAN_WITHOUT_DESIGN = """# Change Plan

## 1. Development Steps

...

## 3. 依赖与执行顺序

none
"""

PLAN_EMPTY_CASES = """# Change Plan

## 4. 测试用例设计

> regression_scope: targeted

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
"""

DIAGNOSIS_WITH_DESIGN = """# Regression Diagnosis

## 问题描述
test bug

## 根因分析
some root cause

## 路由决定
→ executing

## 测试用例设计

> regression_scope: targeted
> 波及接口清单：
> - src/bar.py

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|-------|------|------|---------|--------|
| TC-01 | bar input | expected | AC-01 | P0 |
"""

DIAGNOSIS_WITHOUT_DESIGN = """# Regression Diagnosis

## 问题描述
test bug

## 根因分析
root cause

## 路由决定
→ executing
"""


# ─────────────────────── single-file target tests ────────────────────────


def test_plan_with_design_passes(tmp_path):
    """plan.md with §测试用例设计 section and cases → PASS."""
    root = tmp_path / "repo"
    root.mkdir()
    plan = _write(root / "plan.md", PLAN_WITH_DESIGN)
    rc = check_test_case_design_completeness(root, target_file=plan)
    assert rc == 0


def test_plan_without_design_fails(tmp_path):
    """plan.md without §测试用例设计 → FAIL."""
    root = tmp_path / "repo"
    root.mkdir()
    plan = _write(root / "plan.md", PLAN_WITHOUT_DESIGN)
    rc = check_test_case_design_completeness(root, target_file=plan)
    assert rc == 1


def test_plan_with_empty_cases_fails(tmp_path):
    """plan.md §测试用例设计 with no actual data rows → FAIL."""
    root = tmp_path / "repo"
    root.mkdir()
    plan = _write(root / "plan.md", PLAN_EMPTY_CASES)
    rc = check_test_case_design_completeness(root, target_file=plan)
    assert rc == 1


def test_diagnosis_with_design_passes(tmp_path):
    """bugfix diagnosis.md with §测试用例设计 → PASS."""
    root = tmp_path / "repo"
    root.mkdir()
    diag = _write(root / "regression" / "diagnosis.md", DIAGNOSIS_WITH_DESIGN)
    rc = check_test_case_design_completeness(root, target_file=diag)
    assert rc == 0


def test_diagnosis_without_design_fails(tmp_path):
    """bugfix diagnosis.md without §测试用例设计 → FAIL."""
    root = tmp_path / "repo"
    root.mkdir()
    diag = _write(root / "regression" / "diagnosis.md", DIAGNOSIS_WITHOUT_DESIGN)
    rc = check_test_case_design_completeness(root, target_file=diag)
    assert rc == 1


# ─────────────────────── full-scan tests ────────────────────────


def test_full_scan_flow_bugfixes(tmp_path):
    """Full scan finds bugfix diagnosis.md without §测试用例设计 in flow/bugfixes/."""
    root = tmp_path / "repo"
    root.mkdir()
    diag_dir = root / ".workflow" / "flow" / "bugfixes" / "bugfix-7-test" / "regression"
    diag_dir.mkdir(parents=True)
    (diag_dir / "diagnosis.md").write_text(DIAGNOSIS_WITHOUT_DESIGN, encoding="utf-8")
    rc = check_test_case_design_completeness(root)
    assert rc == 1


def test_full_scan_flow_requirements(tmp_path):
    """Full scan finds plan.md without §测试用例设计 in flow/requirements/."""
    root = tmp_path / "repo"
    root.mkdir()
    chg_dir = root / ".workflow" / "flow" / "requirements" / "req-44-test" / "changes" / "chg-01-test"
    chg_dir.mkdir(parents=True)
    (chg_dir / "plan.md").write_text(PLAN_WITHOUT_DESIGN, encoding="utf-8")
    rc = check_test_case_design_completeness(root)
    assert rc == 1


def test_full_scan_empty_repo_passes(tmp_path):
    """Empty repo with no plan.md/diagnosis.md → PASS (nothing to scan)."""
    root = tmp_path / "repo"
    root.mkdir()
    rc = check_test_case_design_completeness(root)
    assert rc == 0


def test_full_scan_all_passing(tmp_path):
    """All plan.md and diagnosis.md have §测试用例设计 → PASS."""
    root = tmp_path / "repo"
    root.mkdir()
    chg_dir = root / ".workflow" / "flow" / "requirements" / "req-44-test" / "changes" / "chg-01-test"
    chg_dir.mkdir(parents=True)
    (chg_dir / "plan.md").write_text(PLAN_WITH_DESIGN, encoding="utf-8")
    diag_dir = root / ".workflow" / "flow" / "bugfixes" / "bugfix-7-test" / "regression"
    diag_dir.mkdir(parents=True)
    (diag_dir / "diagnosis.md").write_text(DIAGNOSIS_WITH_DESIGN, encoding="utf-8")
    rc = check_test_case_design_completeness(root)
    assert rc == 0


# ─────────────────────── CLI choices test ────────────────────────


def test_cli_contract_choices_include_test_case_design():
    """CLI --contract choices must include test-case-design-completeness."""
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "harness_workflow.cli", "validate", "--contract", "invalid-xxxx"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    # Should fail with 'invalid choice' error mentioning test-case-design-completeness
    combined = result.stdout + result.stderr
    assert "test-case-design-completeness" in combined, (
        f"CLI must list test-case-design-completeness as valid choice, got: {combined[:500]}"
    )


def test_cli_contract_choices_include_artifact_placement():
    """CLI --contract choices must include artifact-placement."""
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "harness_workflow.cli", "validate", "--contract", "invalid-xxxx"],
        capture_output=True, text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    combined = result.stdout + result.stderr
    assert "artifact-placement" in combined, (
        f"CLI must list artifact-placement as valid choice, got: {combined[:500]}"
    )
