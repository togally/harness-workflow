"""req-54（硬门禁体系简化-砍4条降级-加1条项目级brief强约束）/ chg-03（防回归-lint-与dogfood）: 硬门禁体系简化防回归 lint + dogfood。

覆盖：
- TC-01: WORKFLOW.md 全局硬门禁段砍 2 条
- TC-02: base-role.md 硬门禁一 / 二降级（段标题改为指导原则）
- TC-03: base-role.md 硬门禁八整段存在 + boilerplate 字面 + Step 7.6 / 7.6.1
- TC-04: harness-manager.md §3.6 / §3.6.2 含硬门禁八字面
- TC-05: 4 mirror 文件 diff -q 全 silent
- TC-Dogfood-06: fresh repo install --force-managed + validate --contract all 全 PASS
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _env() -> dict:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env


# ============= TC-01：WORKFLOW.md 全局硬门禁段砍 2 条 =============
def test_tc01_workflow_global_hard_gates_reduced_to_two() -> None:
    """WORKFLOW.md `## 全局硬门禁` 段编号行数 ≤ 2。"""
    content = _read("WORKFLOW.md")
    # 找到 `## 全局硬门禁` 起始
    match = re.search(r"^## 全局硬门禁\s*$", content, flags=re.MULTILINE)
    assert match is not None, "WORKFLOW.md 缺失 ## 全局硬门禁 段"
    # 从该位置截到下一个 `## ` 标题
    start = match.end()
    rest = content[start:]
    next_section = re.search(r"^## ", rest, flags=re.MULTILINE)
    section = rest[: next_section.start()] if next_section else rest
    # 数编号行
    enumerated = re.findall(r"^\d+\.\s", section, flags=re.MULTILINE)
    assert len(enumerated) <= 2, (
        f"WORKFLOW.md 全局硬门禁段编号行 {len(enumerated)} > 2 "
        f"（req-54 应砍到 2 条）"
    )


# ============= TC-02：base-role.md 硬门禁一 / 二降级 =============
def test_tc02_base_role_hard_gate_1_2_demoted() -> None:
    """base-role.md 硬门禁一 / 二段标题改为指导原则。"""
    for path in [
        ".workflow/context/roles/base-role.md",
        "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md",
    ]:
        content = _read(path)
        # 命中 1 次「## 工具委派指导原则」+ 1 次「## 操作日志指导原则」
        assert content.count("## 工具委派指导原则") == 1, (
            f"{path} 缺失「## 工具委派指导原则」段标题（chg-01 应改）"
        )
        assert content.count("## 操作日志指导原则") == 1, (
            f"{path} 缺失「## 操作日志指导原则」段标题（chg-01 应改）"
        )
        # 硬门禁清单总览不再含「硬门禁一」「硬门禁二」字面
        # 截 `**硬门禁清单**` 块（约 L15-L25）
        match = re.search(
            r"\*\*硬门禁清单\*\*[：:](.*?)\n## ", content, flags=re.DOTALL
        )
        if match:
            block = match.group(1)
            assert "硬门禁一：工具优先" not in block, (
                f"{path} 硬门禁清单总览仍含「硬门禁一：工具优先」（应移除）"
            )
            assert "硬门禁二：操作说明与日志" not in block, (
                f"{path} 硬门禁清单总览仍含「硬门禁二：操作说明与日志」（应移除）"
            )


# ============= TC-03：base-role.md 硬门禁八整段 =============
def test_tc03_base_role_hard_gate_8_added() -> None:
    """base-role.md 硬门禁八整段存在 + boilerplate + Step 7.6 / 7.6.1。"""
    for path in [
        ".workflow/context/roles/base-role.md",
        "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md",
    ]:
        content = _read(path)
        assert content.count(
            "## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示"
        ) == 1, f"{path} 缺失硬门禁八段标题"
        # 段内含 Step 7.6 / 7.6.1 字面引用
        section_start = content.index(
            "## 硬门禁八：subagent dispatch briefing 必含项目级加载链提示"
        )
        next_section = re.search(r"^## ", content[section_start + 1 :], flags=re.MULTILINE)
        section = (
            content[section_start : section_start + 1 + next_section.start()]
            if next_section
            else content[section_start:]
        )
        assert "Step 7.6" in section, f"{path} 硬门禁八段内缺失 Step 7.6 引用"
        assert "Step 7.6.1" in section, f"{path} 硬门禁八段内缺失 Step 7.6.1 引用"
        # boilerplate 字面：artifacts/project/{constraints,experience,tools}/
        assert "artifacts/project/" in section, (
            f"{path} 硬门禁八段内缺失 artifacts/project/ boilerplate"
        )
        # scope 枚举字面（任一即可）
        assert any(
            kw in section
            for kw in [
                "experience-roles",
                "experience-tool",
                "experience-stage",
                "experience-regression",
                "experience-risk",
            ]
        ), f"{path} 硬门禁八段内缺失 scope 枚举（experience-* 字面）"


# ============= TC-04：harness-manager.md §3.6 / §3.6.2 硬门禁八引用 =============
def test_tc04_harness_manager_section_3_6_2_present() -> None:
    """harness-manager.md §3.6.2 段存在 + 含硬门禁八 + boilerplate。"""
    for path in [
        ".workflow/context/roles/harness-manager.md",
        "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md",
    ]:
        content = _read(path)
        assert "#### 3.6.2 按硬门禁八 brief 项目级加载链" in content, (
            f"{path} 缺失 §3.6.2 子条款标题"
        )
        # §3.6.2 段内含 boilerplate
        idx = content.index("#### 3.6.2 按硬门禁八 brief 项目级加载链")
        next_h4 = re.search(r"^#### ", content[idx + 5 :], flags=re.MULTILINE)
        next_h3 = re.search(r"^### ", content[idx + 5 :], flags=re.MULTILINE)
        end = idx + 5 + min(
            (m.start() for m in [next_h4, next_h3] if m is not None),
            default=len(content),
        )
        section = content[idx:end]
        assert "artifacts/project/" in section, (
            f"{path} §3.6.2 段内缺失 artifacts/project/ boilerplate"
        )
        assert "Step 7.6" in section, f"{path} §3.6.2 段内缺失 Step 7.6 引用"


# ============= TC-05：4 mirror diff -q 全 silent =============
@pytest.mark.parametrize(
    "live_path,mirror_path",
    [
        ("WORKFLOW.md", "src/harness_workflow/assets/scaffold_v2/WORKFLOW.md"),
        (
            ".workflow/context/roles/base-role.md",
            "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/base-role.md",
        ),
        (
            ".workflow/context/roles/harness-manager.md",
            "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/harness-manager.md",
        ),
        (
            ".workflow/context/roles/stage-role.md",
            "src/harness_workflow/assets/scaffold_v2/.workflow/context/roles/stage-role.md",
        ),
    ],
)
def test_tc05_mirror_diff_silent(live_path: str, mirror_path: str) -> None:
    """live 与 mirror 4 对全 silent。"""
    live = REPO_ROOT / live_path
    mirror = REPO_ROOT / mirror_path
    assert live.exists(), f"live 缺失：{live_path}"
    assert mirror.exists(), f"mirror 缺失：{mirror_path}"
    result = subprocess.run(
        ["diff", "-q", str(live), str(mirror)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"live ↔ mirror 漂移：{live_path} vs {mirror_path}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


# ============= TC-Dogfood-06：fresh repo install + validate --contract all =============
def test_tc_dogfood_06_fresh_repo_validate_all_pass(tmp_path: Path) -> None:
    """fresh git init + harness install --force-managed + validate --contract all 全 PASS。

    TC-Dogfood-06 必填字段（sug-52）：
    - 用例名：TC-Dogfood-06
    - tmpdir fixture：tmp_path (pytest builtin)
    - 子进程命令：subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'install', '--force-managed'])
                  subprocess.run([sys.executable, '-m', 'harness_workflow.cli', 'validate', '--contract', 'all'])
    - stdout 断言：returncode == 0（两步均 exit 0）
    - runtime stage 断言：N/A（fresh repo install 后 stage 默认未定义）
    - feedback.jsonl 事件数断言：N/A（本 TC 不涉及 stage 流转，无 stage_advance 事件）
    - 对应 AC：AC-10
    - 优先级：P0
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    # init git
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    # harness install --force-managed
    install_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "harness_workflow.cli",
            "install",
            "--force-managed",
        ],
        cwd=repo,
        env=_env(),
        capture_output=True,
        text=True,
    )
    assert install_result.returncode == 0, (
        f"harness install --force-managed 失败：\n"
        f"stdout: {install_result.stdout}\nstderr: {install_result.stderr}"
    )
    # harness validate --contract all
    validate_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "harness_workflow.cli",
            "validate",
            "--contract",
            "all",
        ],
        cwd=repo,
        env=_env(),
        capture_output=True,
        text=True,
    )
    assert validate_result.returncode == 0, (
        f"harness validate --contract all 失败：\n"
        f"stdout: {validate_result.stdout}\nstderr: {validate_result.stderr}"
    )
