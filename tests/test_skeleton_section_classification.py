"""tests/test_skeleton_section_classification.py

chg-C：路书产品规范完善 + 1.0.0 发版准备

验证 skeleton.py 模板中所有 LLM/USER 区段标记正确分类。

TC-01 overview.md 模板含 LLM:PROJECT_NAME 标记
TC-02 overview.md 模板含 USER:RECENT_CHANGES 标记
TC-03 architecture.md 模板含 LLM:COMPONENT_RELATIONS / LLM:KEY_DEPENDENCIES
TC-04 runbook.md 模板含 4 个 LLM:* 标记（QUICK_START / TEST_COMMANDS / DEPLOY_STEPS / FAQ）
TC-05 code-map.md 模板含 LLM:ENTRY_POINTS / LLM:CONFIG_FILES / LLM:TEST_DIRS
TC-06 domain README 含 LLM:KEY_FILES / LLM:DEPENDENCIES
TC-07 domain data-model 含 3 个 LLM:* 标记（DATA_STRUCTURES / DB_TABLES / DATA_FLOW）
TC-08 domain notes 含 LLM:CROSS_DOMAIN_NOTES + USER:PENDING_DECISIONS + USER:HISTORY
TC-09 区段配对检查（所有模板 LLM/USER 标记均成对）
TC-10 AUTO 区段不受影响（overview AUTO:DOMAIN_LIST 保持）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import (
    _OVERVIEW_TEMPLATE,
    _ARCHITECTURE_TEMPLATE,
    _RUNBOOK_TEMPLATE,
    _CODE_MAP_TEMPLATE,
    _domain_readme_template,
    _domain_data_model_template,
    _domain_notes_template,
)


def _has_llm_section(template: str, name: str) -> bool:
    """检查模板中是否含有 LLM:NAME 开/闭标记对。"""
    return (
        f"<!-- LLM:{name} -->" in template
        and f"<!-- /LLM:{name} -->" in template
    )


def _has_user_section(template: str, name: str) -> bool:
    """检查模板中是否含有 USER:NAME 开/闭标记对。"""
    return (
        f"<!-- USER:{name} -->" in template
        and f"<!-- /USER:{name} -->" in template
    )


def _count_llm_sections(template: str) -> int:
    """统计模板中 LLM:* 开标记数量。"""
    return len(re.findall(r"<!--\s*LLM:\w+\s*-->", template))


def _count_user_sections(template: str) -> int:
    """统计模板中 USER:* 开标记数量。"""
    return len(re.findall(r"<!--\s*USER:\w+\s*-->", template))


# ---------------------------------------------------------------------------
# TC-01: overview.md 含 LLM:PROJECT_NAME
# ---------------------------------------------------------------------------

def test_tc01_overview_llm_project_name():
    """TC-01: overview.md 模板含 LLM:PROJECT_NAME 开/闭标记对。"""
    assert _has_llm_section(_OVERVIEW_TEMPLATE, "PROJECT_NAME"), (
        "Expected <!-- LLM:PROJECT_NAME --> ... <!-- /LLM:PROJECT_NAME --> in overview template"
    )


# ---------------------------------------------------------------------------
# TC-02: overview.md 含 USER:RECENT_CHANGES
# ---------------------------------------------------------------------------

def test_tc02_overview_user_recent_changes():
    """TC-02: overview.md 模板含 USER:RECENT_CHANGES 开/闭标记对。"""
    assert _has_user_section(_OVERVIEW_TEMPLATE, "RECENT_CHANGES"), (
        "Expected <!-- USER:RECENT_CHANGES --> ... <!-- /USER:RECENT_CHANGES --> in overview template"
    )


# ---------------------------------------------------------------------------
# TC-03: architecture.md 含 LLM:COMPONENT_RELATIONS / LLM:KEY_DEPENDENCIES
# ---------------------------------------------------------------------------

def test_tc03_architecture_llm_sections():
    """TC-03: architecture.md 模板含 LLM:COMPONENT_RELATIONS 和 LLM:KEY_DEPENDENCIES 配对。"""
    assert _has_llm_section(_ARCHITECTURE_TEMPLATE, "COMPONENT_RELATIONS"), (
        "Expected <!-- LLM:COMPONENT_RELATIONS --> ... <!-- /LLM:COMPONENT_RELATIONS --> in architecture template"
    )
    assert _has_llm_section(_ARCHITECTURE_TEMPLATE, "KEY_DEPENDENCIES"), (
        "Expected <!-- LLM:KEY_DEPENDENCIES --> ... <!-- /LLM:KEY_DEPENDENCIES --> in architecture template"
    )


# ---------------------------------------------------------------------------
# TC-04: runbook.md 含 4 个 LLM:* 标记
# ---------------------------------------------------------------------------

def test_tc04_runbook_llm_sections():
    """TC-04: runbook.md 模板含 4 个 LLM:* 标记（QUICK_START / TEST_COMMANDS / DEPLOY_STEPS / FAQ）。"""
    assert _has_llm_section(_RUNBOOK_TEMPLATE, "QUICK_START"), (
        "Expected LLM:QUICK_START in runbook template"
    )
    assert _has_llm_section(_RUNBOOK_TEMPLATE, "TEST_COMMANDS"), (
        "Expected LLM:TEST_COMMANDS in runbook template"
    )
    assert _has_llm_section(_RUNBOOK_TEMPLATE, "DEPLOY_STEPS"), (
        "Expected LLM:DEPLOY_STEPS in runbook template"
    )
    assert _has_llm_section(_RUNBOOK_TEMPLATE, "FAQ"), (
        "Expected LLM:FAQ in runbook template"
    )
    count = _count_llm_sections(_RUNBOOK_TEMPLATE)
    assert count == 4, (
        f"Expected 4 LLM:* sections in runbook template, got {count}"
    )


# ---------------------------------------------------------------------------
# TC-05: code-map.md 含 LLM:ENTRY_POINTS / LLM:CONFIG_FILES / LLM:TEST_DIRS
# ---------------------------------------------------------------------------

def test_tc05_code_map_llm_sections():
    """TC-05: code-map.md 模板含 LLM:ENTRY_POINTS / LLM:CONFIG_FILES / LLM:TEST_DIRS。"""
    assert _has_llm_section(_CODE_MAP_TEMPLATE, "ENTRY_POINTS"), (
        "Expected LLM:ENTRY_POINTS in code-map template"
    )
    assert _has_llm_section(_CODE_MAP_TEMPLATE, "CONFIG_FILES"), (
        "Expected LLM:CONFIG_FILES in code-map template"
    )
    assert _has_llm_section(_CODE_MAP_TEMPLATE, "TEST_DIRS"), (
        "Expected LLM:TEST_DIRS in code-map template"
    )


# ---------------------------------------------------------------------------
# TC-06: domain README 含 LLM:KEY_FILES / LLM:DEPENDENCIES
# ---------------------------------------------------------------------------

def test_tc06_domain_readme_llm_sections():
    """TC-06: domain README 模板含 LLM:KEY_FILES 和 LLM:DEPENDENCIES 配对。"""
    template = _domain_readme_template("test_domain")
    assert _has_llm_section(template, "KEY_FILES"), (
        "Expected LLM:KEY_FILES in domain README template"
    )
    assert _has_llm_section(template, "DEPENDENCIES"), (
        "Expected LLM:DEPENDENCIES in domain README template"
    )


# ---------------------------------------------------------------------------
# TC-07: domain data-model 含 3 个 LLM:* 标记
# ---------------------------------------------------------------------------

def test_tc07_domain_data_model_llm_sections():
    """TC-07: domain data-model 模板含 3 个 LLM:* 标记（DATA_STRUCTURES / DB_TABLES / DATA_FLOW）。"""
    template = _domain_data_model_template("test_domain")
    assert _has_llm_section(template, "DATA_STRUCTURES"), (
        "Expected LLM:DATA_STRUCTURES in domain data-model template"
    )
    assert _has_llm_section(template, "DB_TABLES"), (
        "Expected LLM:DB_TABLES in domain data-model template"
    )
    assert _has_llm_section(template, "DATA_FLOW"), (
        "Expected LLM:DATA_FLOW in domain data-model template"
    )
    count = _count_llm_sections(template)
    assert count == 3, (
        f"Expected 3 LLM:* sections in domain data-model template, got {count}"
    )


# ---------------------------------------------------------------------------
# TC-08: domain notes 含 LLM:CROSS_DOMAIN_NOTES + USER:PENDING_DECISIONS + USER:HISTORY
# ---------------------------------------------------------------------------

def test_tc08_domain_notes_sections():
    """TC-08: domain notes 模板含 LLM:CROSS_DOMAIN_NOTES + USER:PENDING_DECISIONS + USER:HISTORY。"""
    template = _domain_notes_template("test_domain")
    assert _has_llm_section(template, "CROSS_DOMAIN_NOTES"), (
        "Expected LLM:CROSS_DOMAIN_NOTES in domain notes template"
    )
    assert _has_user_section(template, "PENDING_DECISIONS"), (
        "Expected USER:PENDING_DECISIONS in domain notes template"
    )
    assert _has_user_section(template, "HISTORY"), (
        "Expected USER:HISTORY in domain notes template"
    )


# ---------------------------------------------------------------------------
# TC-09: 所有 LLM/USER 标记配对完整性
# ---------------------------------------------------------------------------

def test_tc09_all_templates_markers_paired():
    """TC-09: 所有模板中 LLM:*/USER:* 标记均成对（开标记数 = 闭标记数）。"""
    templates = [
        ("overview", _OVERVIEW_TEMPLATE),
        ("architecture", _ARCHITECTURE_TEMPLATE),
        ("runbook", _RUNBOOK_TEMPLATE),
        ("code-map", _CODE_MAP_TEMPLATE),
        ("domain-readme", _domain_readme_template("x")),
        ("domain-data-model", _domain_data_model_template("x")),
        ("domain-notes", _domain_notes_template("x")),
    ]

    for name, template in templates:
        # LLM 配对
        llm_open = re.findall(r"<!--\s*LLM:(\w+)\s*-->", template)
        llm_close = re.findall(r"<!--\s*/LLM:(\w+)\s*-->", template)
        assert sorted(llm_open) == sorted(llm_close), (
            f"Template '{name}': LLM open markers {llm_open} != close markers {llm_close}"
        )

        # USER 配对
        user_open = re.findall(r"<!--\s*USER:(\w+)\s*-->", template)
        user_close = re.findall(r"<!--\s*/USER:(\w+)\s*-->", template)
        assert sorted(user_open) == sorted(user_close), (
            f"Template '{name}': USER open markers {user_open} != close markers {user_close}"
        )


# ---------------------------------------------------------------------------
# TC-10: AUTO 区段不受影响（overview AUTO:DOMAIN_LIST 保持）
# ---------------------------------------------------------------------------

def test_tc10_auto_sections_preserved():
    """TC-10: AUTO 区段不受影响（overview.md AUTO:DOMAIN_LIST / architecture.md AUTO:STACK / AUTO:LAYOUT / AUTO:SCRIPTS）。"""
    # overview.md
    assert "<!-- AUTO:DOMAIN_LIST -->" in _OVERVIEW_TEMPLATE, (
        "Expected AUTO:DOMAIN_LIST in overview template"
    )
    assert "<!-- /AUTO:DOMAIN_LIST -->" in _OVERVIEW_TEMPLATE, (
        "Expected /AUTO:DOMAIN_LIST close tag in overview template"
    )

    # architecture.md
    for marker in ("STACK", "LAYOUT", "SCRIPTS"):
        assert f"<!-- AUTO:{marker} -->" in _ARCHITECTURE_TEMPLATE, (
            f"Expected AUTO:{marker} in architecture template"
        )
        assert f"<!-- /AUTO:{marker} -->" in _ARCHITECTURE_TEMPLATE, (
            f"Expected /AUTO:{marker} close tag in architecture template"
        )
