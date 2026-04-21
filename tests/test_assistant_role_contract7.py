"""req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 4

覆盖 sug-26（辅助角色（harness-manager / tools-manager / reviewer）契约 7 扩展）：
断言三份辅助角色文档 / 清单已补"契约 7"字样及一条 `{id}（{title}）` 形式的示范引用。
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


_FULLWIDTH_ID_TITLE = re.compile(
    r"(?:req|chg|sug|bugfix|reg)-\d+（[^）]+）"
)


def _assert_has_contract_7_and_example(path: Path) -> None:
    assert path.exists(), f"missing doc: {path}"
    text = path.read_text(encoding="utf-8")
    assert "契约 7" in text, f"{path} missing '契约 7' section header"
    assert _FULLWIDTH_ID_TITLE.search(text), (
        f"{path} missing '{{id}}（{{title}}）' example (req-31（批量建议合集（20条）) style)"
    )


def test_harness_manager_md_contains_contract_7() -> None:
    _assert_has_contract_7_and_example(
        REPO_ROOT / ".workflow/context/roles/harness-manager.md"
    )


def test_tools_manager_md_contains_contract_7() -> None:
    _assert_has_contract_7_and_example(
        REPO_ROOT / ".workflow/context/roles/tools-manager.md"
    )


def test_review_checklist_contains_contract_7() -> None:
    _assert_has_contract_7_and_example(
        REPO_ROOT / ".workflow/context/checklists/review-checklist.md"
    )
