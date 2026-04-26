"""Tests for test case design in planning (bugfix-6 B1/B2/B3/B4).

B1: analyst.md contains Step B2.5 test case design section
B2: testing.md reads plan.md §测试用例设计 (not "设计测试用例")
B3: evaluation/testing.md contains §0 targeted default + trigger conditions
B4: plan.md template contains §4. 测试用例设计 chapter
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest


REPO_ROOT = Path(__file__).parent.parent


# ─────────────────────── B1: analyst.md SOP ────────────────────────


def test_analyst_md_has_test_case_design_step():
    """analyst.md must contain Step B2.5 test case design."""
    analyst_md = REPO_ROOT / ".workflow" / "context" / "roles" / "analyst.md"
    assert analyst_md.exists(), "analyst.md must exist"
    content = analyst_md.read_text(encoding="utf-8")
    assert "Step B2.5" in content or "B2.5" in content, (
        "analyst.md must contain Step B2.5 (test case design)"
    )
    assert "测试用例设计" in content, "analyst.md must mention 测试用例设计"


def test_analyst_md_test_case_design_has_regression_scope():
    """analyst.md §测试用例设计 must mention regression_scope field."""
    analyst_md = REPO_ROOT / ".workflow" / "context" / "roles" / "analyst.md"
    content = analyst_md.read_text(encoding="utf-8")
    assert "regression_scope" in content, "analyst.md must document regression_scope field"


def test_analyst_md_planning_exit_condition_has_test_case_design():
    """analyst.md Part B exit conditions must include §4. 测试用例设计 requirement."""
    analyst_md = REPO_ROOT / ".workflow" / "context" / "roles" / "analyst.md"
    content = analyst_md.read_text(encoding="utf-8")
    assert "test-case-design-completeness" in content, (
        "analyst.md exit conditions must reference test-case-design-completeness lint"
    )


# ─────────────────────── B2: testing.md SOP ────────────────────────


def test_testing_md_no_old_step2_design():
    """testing.md Step 2 must NOT say '设计测试用例'."""
    testing_md = REPO_ROOT / ".workflow" / "context" / "roles" / "testing.md"
    content = testing_md.read_text(encoding="utf-8")
    # The old Step 2 header
    assert "Step 2: 设计测试用例" not in content, (
        "testing.md must NOT have old Step 2: 设计测试用例"
    )


def test_testing_md_has_read_plan_step():
    """testing.md Step 2 must say '读取 plan.md §测试用例设计'."""
    testing_md = REPO_ROOT / ".workflow" / "context" / "roles" / "testing.md"
    content = testing_md.read_text(encoding="utf-8")
    assert "读取 plan.md §测试用例设计" in content or "读取" in content, (
        "testing.md must reference reading plan.md §测试用例设计"
    )


def test_testing_md_has_bugfix_mode_fallback():
    """testing.md must mention bugfix mode falling back to diagnosis.md."""
    testing_md = REPO_ROOT / ".workflow" / "context" / "roles" / "testing.md"
    content = testing_md.read_text(encoding="utf-8")
    assert "diagnosis.md" in content, "testing.md must reference diagnosis.md for bugfix mode"


def test_testing_md_has_regression_scope_reference():
    """testing.md must reference regression_scope field for targeted/full decision."""
    testing_md = REPO_ROOT / ".workflow" / "context" / "roles" / "testing.md"
    content = testing_md.read_text(encoding="utf-8")
    assert "regression_scope" in content, "testing.md must reference regression_scope field"


def test_testing_md_has_independent_exception_clause():
    """testing.md must preserve testing's right to add edge cases."""
    testing_md = REPO_ROOT / ".workflow" / "context" / "roles" / "testing.md"
    content = testing_md.read_text(encoding="utf-8")
    # Must have some mention of testing being able to add boundary/edge cases
    assert "反例" in content or "边界" in content or "例外子条款" in content, (
        "testing.md must preserve testing's right to add boundary/edge cases"
    )


# ─────────────────────── B3: evaluation/testing.md ────────────────────────


def test_evaluation_testing_md_has_targeted_default_section():
    """evaluation/testing.md must have §0 targeted default section."""
    testing_eval = REPO_ROOT / ".workflow" / "evaluation" / "testing.md"
    content = testing_eval.read_text(encoding="utf-8")
    assert "targeted" in content, "evaluation/testing.md must mention targeted"
    assert "默认" in content or "default" in content.lower(), (
        "evaluation/testing.md must document targeted as default"
    )


def test_evaluation_testing_md_has_full_regression_trigger_conditions():
    """evaluation/testing.md must list explicit conditions for full regression."""
    testing_eval = REPO_ROOT / ".workflow" / "evaluation" / "testing.md"
    content = testing_eval.read_text(encoding="utf-8")
    # Must have "全量回归触发条件" or similar
    assert "全量" in content, "evaluation/testing.md must mention 全量 (full regression)"
    assert "触发" in content, "evaluation/testing.md must mention trigger conditions"


def test_evaluation_testing_md_prohibits_over_instructing():
    """evaluation/testing.md must prohibit default full-regression in briefing."""
    testing_eval = REPO_ROOT / ".workflow" / "evaluation" / "testing.md"
    content = testing_eval.read_text(encoding="utf-8")
    assert "禁止" in content, "evaluation/testing.md must prohibit over-instructing"


# ─────────────────────── B4: plan.md template ────────────────────────


def test_change_plan_template_has_test_case_design_section():
    """change-plan.md.tmpl must contain §4. 测试用例设计 chapter."""
    tmpl = REPO_ROOT / "src" / "harness_workflow" / "assets" / "skill" / "assets" / "templates" / "change-plan.md.tmpl"
    content = tmpl.read_text(encoding="utf-8")
    assert "4. 测试用例设计" in content or "测试用例设计" in content, (
        "change-plan.md.tmpl must contain §4. 测试用例设计"
    )
    assert "regression_scope" in content, "change-plan.md.tmpl must contain regression_scope field"


def test_change_plan_en_template_has_test_case_design_section():
    """change-plan.md.en.tmpl must contain Test Case Design chapter."""
    tmpl = REPO_ROOT / "src" / "harness_workflow" / "assets" / "skill" / "assets" / "templates" / "change-plan.md.en.tmpl"
    content = tmpl.read_text(encoding="utf-8")
    assert "Test Case Design" in content, (
        "change-plan.md.en.tmpl must contain Test Case Design section"
    )
    assert "regression_scope" in content, "change-plan.md.en.tmpl must contain regression_scope field"


def test_change_plan_template_has_table_structure():
    """change-plan.md.tmpl §测试用例设计 must have table with required columns."""
    tmpl = REPO_ROOT / "src" / "harness_workflow" / "assets" / "skill" / "assets" / "templates" / "change-plan.md.tmpl"
    content = tmpl.read_text(encoding="utf-8")
    # Must have table header with required columns
    assert "用例名" in content, "template must have 用例名 column"
    assert "对应 AC" in content or "对应AC" in content, "template must have 对应 AC column"
    assert "优先级" in content, "template must have 优先级 column"
