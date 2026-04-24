"""req-31（批量建议合集（20条））/ chg-01（契约自动化 + apply-all bug）/ Step 2+3

TDD 测试：`check_contract_7` helper + `harness status --lint` CLI 入口
（覆盖 sug-25 `harness status --lint` 自动化契约 7 校验）。

- 红色阶段：validate_contract 模块尚未存在；这些用例先 import 失败 → 实现后转绿。
- 合规样本：行内首次 id 带 `（title）` 或 `(title)` 即通过。
- 违规样本：行内首次裸 id（无紧邻括号标题）判违规。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _write(tmp: Path, rel: str, content: str) -> Path:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return p


def test_check_contract_7_reports_bare_id(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_7

    f = _write(tmp_path, "artifacts/main/requirements/req-99/requirement.md", "# req-99 demo\n- see req-99 for detail\n")
    violations = check_contract_7(tmp_path, [f])
    assert len(violations) == 1, f"expected 1 violation, got {violations}"
    v = violations[0]
    assert v.work_item_id == "req-99"
    assert v.line == 1
    assert str(f.relative_to(tmp_path)) in str(v.file.relative_to(tmp_path))


def test_check_contract_7_passes_on_id_with_title_fullwidth(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_7

    f = _write(tmp_path, "artifacts/main/ok.md", "本文档涉及 req-99（Demo 需求 标题）和后续 req-99 简写\n")
    violations = check_contract_7(tmp_path, [f])
    assert violations == [], f"expected 0 violations, got {violations}"


def test_check_contract_7_passes_on_id_with_title_halfwidth(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_7

    f = _write(tmp_path, "artifacts/main/ok2.md", "Ref: req-99 (Demo requirement title) plus bare req-99 later\n")
    violations = check_contract_7(tmp_path, [f])
    assert violations == []


def test_check_contract_7_multiple_files_multiple_ids(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_7

    f1 = _write(tmp_path, "a.md", "Hit req-01 and chg-01 no title\n")
    f2 = _write(tmp_path, "b.md", "Good req-02（t2）bad sug-99 bare\n")
    violations = check_contract_7(tmp_path, [f1, f2])
    ids = sorted((v.work_item_id, v.file.name) for v in violations)
    # f1: both req-01 and chg-01 bare; f2: only sug-99 bare (req-02 compliant)
    assert ("chg-01", "a.md") in ids
    assert ("req-01", "a.md") in ids
    assert ("sug-99", "b.md") in ids
    assert len(ids) == 3


def test_check_contract_3_4_regression_missing_file(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_3_4_regression

    reg_dir = tmp_path / "artifacts/main/requirements/req-1/regressions/reg-01"
    reg_dir.mkdir(parents=True)
    issues = check_contract_3_4_regression(tmp_path, reg_dir)
    assert len(issues) == 1
    assert "回归简报.md" in issues[0]


def test_check_contract_3_4_regression_present_and_complete(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_3_4_regression

    reg_dir = tmp_path / "artifacts/main/requirements/req-1/regressions/reg-01"
    reg_dir.mkdir(parents=True)
    (reg_dir / "回归简报.md").write_text(
        "# 回归简报：reg-01 demo issue\n\n"
        "## 问题\n- x\n\n"
        "## 根因\n- y\n\n"
        "## 影响\n- z\n\n"
        "## 路由决策\n- testing\n",
        encoding="utf-8",
    )
    issues = check_contract_3_4_regression(tmp_path, reg_dir)
    assert issues == []


def test_check_contract_3_4_regression_missing_sections(tmp_path: Path) -> None:
    from harness_workflow.validate_contract import check_contract_3_4_regression

    reg_dir = tmp_path / "artifacts/main/requirements/req-1/regressions/reg-01"
    reg_dir.mkdir(parents=True)
    (reg_dir / "回归简报.md").write_text("# 回归简报\n## 问题\n- x\n", encoding="utf-8")
    issues = check_contract_3_4_regression(tmp_path, reg_dir)
    assert issues  # should flag missing sections


def test_workflow_status_lint_passes_when_clean(tmp_path: Path) -> None:
    """harness status --lint 对干净仓库返回 0。"""
    from harness_workflow.workflow_helpers import workflow_status_lint

    (tmp_path / ".workflow/state").mkdir(parents=True)
    # 没有 artifacts 目录 → 0 违规
    assert workflow_status_lint(tmp_path) == 0


def test_workflow_status_lint_fails_on_bare_id(tmp_path: Path) -> None:
    from harness_workflow.workflow_helpers import workflow_status_lint

    (tmp_path / ".workflow/state").mkdir(parents=True)
    _write(tmp_path, "artifacts/main/requirements/req-1/实施说明.md", "See chg-77 for detail\n")
    assert workflow_status_lint(tmp_path) == 1


def test_status_cli_lint_flag_exit_nonzero(tmp_path: Path) -> None:
    """Integration: `harness status --lint` 命中违规时非零退出。"""
    import os

    (tmp_path / ".workflow/state").mkdir(parents=True)
    _write(tmp_path, "artifacts/main/requirements/req-1/实施说明.md", "See sug-77 bare\n")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow", "status", "--lint", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1, f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    assert "contract-7" in result.stdout


def test_check_contract_7_skips_id_inside_code_fence(tmp_path: Path) -> None:
    """req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）：
    三反引号代码块内的裸 id 不应命中（过去会命中）。
    """
    from harness_workflow.validate_contract import check_contract_7

    content = (
        "# doc\n"
        "正文首次引用 req-38（api-document-upload 工具闭环）合规。\n"
        "```markdown\n"
        "反例：req-38 裸 id 在代码块内，不应命中\n"
        "```\n"
    )
    f = _write(tmp_path, "artifacts/main/requirements/req-38/plan.md", content)
    violations = check_contract_7(tmp_path, [f])
    assert violations == [], (
        f"expected 0 violations (code fence content skipped), got {violations}"
    )


def test_check_contract_7_still_catches_bare_id_outside_code_fence(tmp_path: Path) -> None:
    """req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）：
    代码块外的裸 chg-01 仍应命中，保持原有扫描行为不变。
    """
    from harness_workflow.validate_contract import check_contract_7

    content = (
        "# doc\n"
        "```markdown\n"
        "代码块内的内容不计\n"
        "```\n"
        "代码块外裸引用 chg-01 无 title，应命中。\n"
    )
    f = _write(tmp_path, "artifacts/main/requirements/req-38/change.md", content)
    violations = check_contract_7(tmp_path, [f])
    assert len(violations) == 1, f"expected 1 violation (chg-01 bare outside fence), got {violations}"
    assert violations[0].work_item_id == "chg-01"


def test_check_contract_7_skips_id_inside_inline_backtick(tmp_path: Path) -> None:
    """req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）：
    inline 单反引号代码 span（`chg-01`）内的裸 id 不应命中。
    """
    from harness_workflow.validate_contract import check_contract_7

    content = (
        "# doc\n"
        "锚点行：`chg-01` 在 inline 代码 span 内，不应命中违规。\n"
    )
    f = _write(tmp_path, "artifacts/main/requirements/req-38/plan.md", content)
    violations = check_contract_7(tmp_path, [f])
    assert violations == [], (
        f"expected 0 violations (inline backtick span skipped), got {violations}"
    )


def test_check_contract_7_catches_bare_id_not_in_backtick(tmp_path: Path) -> None:
    """req-38（api-document-upload 工具闭环）/ chg-06（硬门禁六 + 契约 7 批量列举子条款补丁）：
    inline 反引号之外的裸 chg-01 仍应命中。
    """
    from harness_workflow.validate_contract import check_contract_7

    content = (
        "# doc\n"
        "这里有 chg-01 裸引用（无 title），应命中违规；`req-38` 在 span 内不计。\n"
    )
    f = _write(tmp_path, "artifacts/main/requirements/req-38/plan.md", content)
    violations = check_contract_7(tmp_path, [f])
    assert len(violations) == 1, f"expected 1 violation (chg-01 bare outside backtick), got {violations}"
    assert violations[0].work_item_id == "chg-01"
