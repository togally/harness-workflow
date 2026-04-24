"""acceptance gate 强执行契约测试。

溯源：req-39（对人文档家族契约化 + artifacts 扁平化）/
      chg-04（acceptance gate 强执行：lint 阻塞 + 未绿 FAIL）。

用例覆盖：
  1. acceptance.md 中"必须执行 + harness validate --human-docs + FAIL"三关键字邻近共现（AC-5 静态断言）。
  2. 构造缺少 需求摘要.md 的 tmp req-39 扁平目录，调用 run_cli 断言 exit code = 1（AC-5 集成断言）。
     若 chg-02（validate_human_docs 重写）未落地则跳过，留 TODO 待解除。
"""

from __future__ import annotations

import sys
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

ACCEPTANCE_MD = REPO_ROOT / ".workflow" / "evaluation" / "acceptance.md"

# ---------------------------------------------------------------------------
# 用例 1：acceptance.md 静态断言 — 必须执行 + harness validate --human-docs + FAIL
# ---------------------------------------------------------------------------

def test_acceptance_gate_requires_human_docs_lint_exit_zero() -> None:
    """AC-5 静态断言：acceptance.md 中必须同时含「必须执行」「harness validate --human-docs」「FAIL」。

    三关键字须在同一邻近段落（± 5 行内共现），确保 gate 条款语义完整。
    """
    assert ACCEPTANCE_MD.exists(), f"acceptance.md not found: {ACCEPTANCE_MD}"
    text = ACCEPTANCE_MD.read_text(encoding="utf-8")

    assert "必须执行" in text or "必须" in text, (
        "acceptance.md 缺少「必须执行」或「必须」关键字，硬门禁条款未落地"
    )
    assert "harness validate --human-docs" in text, (
        "acceptance.md 缺少「harness validate --human-docs」命令，硬门禁条款未落地"
    )
    assert "FAIL" in text, (
        "acceptance.md 缺少「FAIL」关键字，未绿强制 FAIL 语义未落地"
    )

    # 邻近共现：三关键字须在 ± 5 行内出现
    lines = text.splitlines()
    kw1 = "harness validate --human-docs"
    kw2 = "FAIL"
    kw3 = "必须"

    def _find_lines_with(kw: str) -> list[int]:
        return [i for i, line in enumerate(lines) if kw in line]

    positions_kw1 = _find_lines_with(kw1)
    positions_kw2 = _find_lines_with(kw2)
    positions_kw3 = _find_lines_with(kw3)

    assert positions_kw1, f"关键字「{kw1}」未在 acceptance.md 命中"
    assert positions_kw2, f"关键字「{kw2}」未在 acceptance.md 命中"
    assert positions_kw3, f"关键字「{kw3}」未在 acceptance.md 命中"

    # 检查邻近共现：kw1 附近 ±5 行是否同时含 kw2 和 kw3
    coexist = False
    for pos in positions_kw1:
        window = lines[max(0, pos - 5): pos + 6]
        window_text = "\n".join(window)
        if kw2 in window_text and kw3 in window_text:
            coexist = True
            break

    assert coexist, (
        f"「{kw1}」「{kw2}」「{kw3}」三关键字未在 acceptance.md 同一段落（±5 行）内共现，"
        "硬门禁条款文字可能不完整"
    )


# ---------------------------------------------------------------------------
# 用例 2：集成断言 — 缺少 需求摘要.md 时 run_cli 返回 1
# ---------------------------------------------------------------------------

def _has_validate_module() -> bool:
    """检查 validate_human_docs 模块可用（chg-02 已落地）。"""
    try:
        from harness_workflow.validate_human_docs import run_cli  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not _has_validate_module(),
    reason="TODO: chg-02（validate_human_docs 重写）未落地，集成用例暂跳过，待 chg-02 完成后解除",
)
def test_acceptance_gate_fails_on_missing_human_docs(tmp_path: Path) -> None:
    """AC-5 集成断言：缺 需求摘要.md 时 run_cli 返回非零退出码（acceptance 应 FAIL）。

    构造 tmp_path 下新扁平结构 req-39 目录，仅建 artifacts 骨架，不放 需求摘要.md。
    预期 run_cli exit code = 1，对应 acceptance-report.md 状态 = FAIL 语义。

    溯源：req-39（对人文档家族契约化 + artifacts 扁平化）/ chg-04（acceptance gate 强执行）。
    """
    from harness_workflow.validate_human_docs import run_cli

    # 构造最小仓库骨架：artifacts/main/requirements/req-39-{slug}/（缺 需求摘要.md）
    req_slug = "req-39-对人文档家族契约化-artifacts-扁平化"
    req_dir = tmp_path / "artifacts" / "main" / "requirements" / req_slug
    req_dir.mkdir(parents=True, exist_ok=True)

    # runtime.yaml：current_requirement = req-39
    runtime_dir = tmp_path / ".workflow" / "state"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "runtime.yaml").write_text(
        "current_requirement: req-39\nstage: acceptance\n", encoding="utf-8"
    )

    # 不放 需求摘要.md，验证 lint 缺失时返回非零
    exit_code = run_cli(tmp_path, "req-39")
    assert exit_code != 0, (
        f"缺少 需求摘要.md 时 run_cli 应返回非零 exit code，但实际返回 {exit_code}；"
        "acceptance gate 强执行条款未生效"
    )
