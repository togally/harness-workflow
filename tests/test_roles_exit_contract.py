"""
Pytest: role exit contract static assertions.

Traceability:
  - req-39（对人文档家族契约化 + artifacts 扁平化）
  - chg-03（requirement-review / planning 自检硬门禁代码化）

These tests use grep-style assertions to verify that the exit conditions
of requirement-review.md and planning.md include the mandatory
`harness validate --human-docs` hard gate (硬门禁), preventing agent
pass-through without lint clearance.
"""

import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).parent.parent
ROLES_DIR = REPO_ROOT / ".workflow" / "context" / "roles"


def _load_role(filename: str) -> str:
    path = ROLES_DIR / filename
    assert path.exists(), f"Role file not found: {path}"
    return path.read_text(encoding="utf-8")


def _lines_near(text: str, keyword: str, window: int = 3) -> list[str]:
    """Return all lines within ±window of any line containing keyword."""
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines):
        if keyword in line:
            start = max(0, i - window)
            end = min(len(lines), i + window + 1)
            result.extend(lines[start:end])
    return result


def test_requirement_review_exit_requires_human_docs_lint():
    """
    AC-3 assertion: .workflow/context/roles/requirement-review.md must contain
    both 'harness validate --human-docs' and 'ABORT' in proximity (±3 lines)
    within the exit conditions section.

    Covers: req-39 / chg-03 / AC-3
    """
    content = _load_role("requirement-review.md")

    # Assert harness validate --human-docs appears at least once
    assert "harness validate --human-docs" in content, (
        "requirement-review.md must contain 'harness validate --human-docs' "
        "in exit conditions (chg-03 / AC-3)"
    )

    # Assert ABORT appears at least once
    assert "ABORT" in content, (
        "requirement-review.md must contain 'ABORT' to indicate failure path "
        "when lint does not pass (chg-03 / AC-3)"
    )

    # Assert co-occurrence: ABORT and harness validate --human-docs within ±3 lines
    lines_near_validate = _lines_near(content, "harness validate --human-docs", window=3)
    abort_near_validate = any("ABORT" in line for line in lines_near_validate)

    lines_near_abort = _lines_near(content, "ABORT", window=3)
    validate_near_abort = any("harness validate --human-docs" in line for line in lines_near_abort)

    assert abort_near_validate or validate_near_abort, (
        "requirement-review.md: 'ABORT' must appear within ±3 lines of "
        "'harness validate --human-docs' (chg-03 / AC-3 proximity check)"
    )


def test_planning_exit_requires_per_chg_brief_lint():
    """
    AC-4 assertion: .workflow/context/roles/planning.md must contain
    'harness validate --human-docs' and a per-chg brief requirement
    ('每 chg 一份' or 'chg-NN-变更简报.md') in proximity (±3 lines).

    Covers: req-39 / chg-03 / AC-4
    """
    content = _load_role("planning.md")

    # Assert harness validate --human-docs appears at least once
    assert "harness validate --human-docs" in content, (
        "planning.md must contain 'harness validate --human-docs' "
        "in exit conditions (chg-03 / AC-4)"
    )

    # Assert per-chg brief requirement appears
    has_per_chg = "每 chg 一份" in content or "chg-NN-变更简报.md" in content
    assert has_per_chg, (
        "planning.md must contain '每 chg 一份' or 'chg-NN-变更简报.md' "
        "to enforce per-change brief requirement (chg-03 / AC-4)"
    )

    # Assert co-occurrence within ±3 lines
    lines_near_validate = _lines_near(content, "harness validate --human-docs", window=3)
    per_chg_near_validate = any(
        "每 chg 一份" in line or "chg-NN-变更简报.md" in line
        for line in lines_near_validate
    )

    lines_near_per_chg_1 = _lines_near(content, "每 chg 一份", window=3)
    lines_near_per_chg_2 = _lines_near(content, "chg-NN-变更简报.md", window=3)
    validate_near_per_chg = any(
        "harness validate --human-docs" in line
        for line in lines_near_per_chg_1 + lines_near_per_chg_2
    )

    assert per_chg_near_validate or validate_near_per_chg, (
        "planning.md: '每 chg 一份' or 'chg-NN-变更简报.md' must appear within ±3 lines of "
        "'harness validate --human-docs' (chg-03 / AC-4 proximity check)"
    )
