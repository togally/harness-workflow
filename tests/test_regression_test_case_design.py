"""Tests for bugfix regression §测试用例设计 section (bugfix-6 C1/C2/C3).

C1: regression.md SOP has Step 4.5 (测试用例设计 for bugfix mode)
C2: evaluation/regression.md has §测试用例设计 block in template
C3: test-case-design-completeness lint covers bugfix flow/bugfixes/ diagnosis.md
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from harness_workflow.validate_contract import check_test_case_design_completeness


REPO_ROOT = Path(__file__).parent.parent


# ─────────────────────── C1: regression.md SOP ────────────────────────


def test_regression_md_has_step_4_5():
    """regression.md must contain Step 4.5 for test case design in bugfix mode."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    assert regression_md.exists(), "regression.md must exist"
    content = regression_md.read_text(encoding="utf-8")
    assert "Step 4.5" in content or "4.5" in content, (
        "regression.md must contain Step 4.5 (测试用例设计 for bugfix mode)"
    )


def test_regression_md_step_4_5_is_bugfix_mode_only():
    """regression.md Step 4.5 must be scoped to bugfix mode."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    content = regression_md.read_text(encoding="utf-8")
    assert "bugfix 模式" in content or "bugfix mode" in content.lower(), (
        "regression.md Step 4.5 must be scoped to bugfix mode"
    )


def test_regression_md_step_4_5_has_diagnosis_md_target():
    """regression.md Step 4.5 must target diagnosis.md."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    content = regression_md.read_text(encoding="utf-8")
    assert "diagnosis.md" in content, "regression.md must reference diagnosis.md as target"


def test_regression_md_exit_condition_has_test_case_design():
    """regression.md exit conditions must include §测试用例设计 for bugfix mode."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    content = regression_md.read_text(encoding="utf-8")
    assert "test-case-design-completeness" in content, (
        "regression.md exit conditions must reference test-case-design-completeness lint"
    )


def test_regression_md_has_regression_scope_reference():
    """regression.md must document regression_scope field."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    content = regression_md.read_text(encoding="utf-8")
    assert "regression_scope" in content, (
        "regression.md must document regression_scope field"
    )


def test_regression_md_step_4_5_has_table_structure():
    """regression.md Step 4.5 must describe table structure for test cases."""
    regression_md = REPO_ROOT / ".workflow" / "context" / "roles" / "regression.md"
    content = regression_md.read_text(encoding="utf-8")
    assert "用例名" in content, "regression.md must define 用例名 column"
    assert "对应 AC" in content or "对应AC" in content, "regression.md must define AC column"


# ─────────────────────── C2: evaluation/regression.md ────────────────────────


def test_evaluation_regression_md_has_test_case_design():
    """evaluation/regression.md must mention 测试用例设计."""
    eval_regression = REPO_ROOT / ".workflow" / "evaluation" / "regression.md"
    assert eval_regression.exists(), "evaluation/regression.md must exist"
    content = eval_regression.read_text(encoding="utf-8")
    assert "测试用例设计" in content, (
        "evaluation/regression.md must contain §测试用例设计 section"
    )


def test_evaluation_regression_md_has_diagnosis_template_block():
    """evaluation/regression.md diagnosis.md template must include §测试用例设计."""
    eval_regression = REPO_ROOT / ".workflow" / "evaluation" / "regression.md"
    content = eval_regression.read_text(encoding="utf-8")
    assert "regression_scope" in content, (
        "evaluation/regression.md must document regression_scope in diagnosis template"
    )


def test_evaluation_regression_md_mentions_b5_lint():
    """evaluation/regression.md must reference B5 lint (test-case-design-completeness)."""
    eval_regression = REPO_ROOT / ".workflow" / "evaluation" / "regression.md"
    content = eval_regression.read_text(encoding="utf-8")
    assert "test-case-design-completeness" in content, (
        "evaluation/regression.md must reference test-case-design-completeness lint"
    )


def test_evaluation_regression_md_bugfix_mode_required():
    """evaluation/regression.md must mark §测试用例设计 as required for bugfix mode."""
    eval_regression = REPO_ROOT / ".workflow" / "evaluation" / "regression.md"
    content = eval_regression.read_text(encoding="utf-8")
    assert "bugfix 模式必填" in content or "必填" in content, (
        "evaluation/regression.md must mark §测试用例设计 as required for bugfix mode"
    )


# ─────────────────────── C3: B5 lint covers bugfix flow ────────────────────────


def test_b5_lint_covers_flow_bugfixes_diagnosis(tmp_path):
    """C3: B5 lint scans .workflow/flow/bugfixes/*/regression/diagnosis.md."""
    root = tmp_path / "repo"
    root.mkdir()
    # Create bugfix diagnosis.md WITHOUT §测试用例设计
    diag_dir = root / ".workflow" / "flow" / "bugfixes" / "bugfix-7-test" / "regression"
    diag_dir.mkdir(parents=True)
    (diag_dir / "diagnosis.md").write_text(
        "# Regression Diagnosis\n## 根因分析\nsome root cause\n",
        encoding="utf-8",
    )
    rc = check_test_case_design_completeness(root)
    assert rc == 1, "B5 lint must detect missing §测试用例设计 in bugfix diagnosis.md"


def test_b5_lint_passes_for_complete_bugfix_diagnosis(tmp_path):
    """C3: B5 lint passes when diagnosis.md has valid §测试用例设计."""
    root = tmp_path / "repo"
    root.mkdir()
    diag_dir = root / ".workflow" / "flow" / "bugfixes" / "bugfix-7-test" / "regression"
    diag_dir.mkdir(parents=True)
    (diag_dir / "diagnosis.md").write_text(
        "# Regression Diagnosis\n\n## 根因分析\nroot cause\n\n"
        "## 测试用例设计\n\n> regression_scope: targeted\n\n"
        "| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |\n"
        "|-------|------|------|---------|--------|\n"
        "| TC-01 | input | output | AC-01 | P0 |\n",
        encoding="utf-8",
    )
    rc = check_test_case_design_completeness(root)
    assert rc == 0, "B5 lint must PASS when diagnosis.md has valid §测试用例设计"


def test_b5_lint_does_not_scan_artifacts_diagnosis(tmp_path):
    """B5 lint must NOT scan artifacts/ for diagnosis.md (only flow/)."""
    root = tmp_path / "repo"
    root.mkdir()
    # Put a diagnosis.md in artifacts/ (violation, but B5 lint doesn't look there)
    diag_dir = root / "artifacts" / "main" / "bugfixes" / "bugfix-5-test" / "regression"
    diag_dir.mkdir(parents=True)
    (diag_dir / "diagnosis.md").write_text(
        "# diag without §测试用例设计",
        encoding="utf-8",
    )
    # B5 lint should not scan artifacts/ - only flow/
    rc = check_test_case_design_completeness(root)
    # Since there's nothing in .workflow/flow/, should PASS
    assert rc == 0, "B5 lint must not scan artifacts/ for diagnosis.md"
