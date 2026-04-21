"""req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 5-6

覆盖 sug-10（regression 阶段《回归简报.md》契约执行补强）+ sug-15（产出对人文档后自动 `harness validate`）：
- `regression.md` 退出条件含 `harness validate --regression` 自检
- `stage-role.md` 契约 4 升格段含"产出对人文档后 MUST 触发 `harness validate --contract`"子条款
- `check_contract_3_4_regression` 已在 test_contract7_lint 覆盖
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_regression_md_exit_contains_validate_regression() -> None:
    path = REPO_ROOT / ".workflow/context/roles/regression.md"
    text = path.read_text(encoding="utf-8")
    # 退出条件 / 完成前检查段含 `harness validate --contract regression`
    assert "harness validate --contract regression" in text or "harness validate --regression" in text, (
        "regression.md missing 'harness validate --contract regression' exit condition (sug-10)"
    )


def test_stage_role_contract_4_upgrade_references_harness_validate() -> None:
    path = REPO_ROOT / ".workflow/context/roles/stage-role.md"
    text = path.read_text(encoding="utf-8")
    # 契约 4 章节末尾升格条款包含 `harness validate --contract`
    assert "harness validate --contract" in text, (
        "stage-role.md contract 4 missing 'harness validate --contract' upgrade clause (sug-15)"
    )
