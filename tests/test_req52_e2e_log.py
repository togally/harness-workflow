"""req-52 / chg-04：端到端真实 CLI 触发 + stderr 日志断言（OQ-D = A）。

用例：
- TC-01-zero-files：项目级 0 文件（无 artifacts/project/，无 legacy）→ stderr 含 "0 files"
- TC-02-main-path-hit：项目级 ≥ 1 文件（artifacts/project/constraints/rule.md）→ stderr 含 "from artifacts/project/constraints/" + ≥ 1 file
- TC-03-legacy-fallback：仅 artifacts/{branch}/project/ 有文件 → stderr 含 "fallback=主路径" 提示

测试触发方式：subprocess.run([sys.executable, "-m", "harness_workflow.cli", "install", "--check"]) 真实子进程。
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

REPO_ROOT = _REPO_ROOT


def _run_harness_install_check(cwd: Path) -> subprocess.CompletedProcess:
    """子进程触发真实 CLI `harness install --check`。"""
    env = dict(os.environ)
    # 让子进程能找到 harness_workflow 包
    env["PYTHONPATH"] = str(REPO_ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", "--check"],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


def _bootstrap_minimal_repo(target: Path) -> None:
    """在 target 创建一个最小可跑 harness install --check 的仓骨架。

    复制必要的 .workflow/ 子树（仅 contract / runtime 必需文件）；
    init git repo 以便 _get_git_branch 不报错。
    """
    # 复制 scaffold_v2 mirror 作为最小骨架
    scaffold = REPO_ROOT / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    shutil.copytree(scaffold, target, dirs_exist_ok=True)
    # init git
    subprocess.run(["git", "init", "-q"], cwd=str(target), check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "main"], cwd=str(target), check=False)


def test_zero_files_e2e(tmp_path):
    """TC-01：项目级 0 文件 → stderr 含 'project-level loaded: 0 files'。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)
    # 不创建 artifacts/project/* 任何子目录

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言三 scope 各有 1 行 "0 files"
    assert "[harness] project-level loaded: 0 files" in result.stderr, (
        f"stderr 缺少零文件日志：{result.stderr}"
    )
    # 三 scope 各一次（≥ 3 行）
    count = result.stderr.count("[harness] project-level loaded:")
    assert count >= 3, f"期望 ≥ 3 行 project-level loaded（constraints/experience/tools），实际 {count} 行：{result.stderr}"


def test_main_path_hit_e2e(tmp_path):
    """TC-02：项目级 ≥ 1 文件（主路径 artifacts/project/constraints/rule.md）→ stderr 含 'from artifacts/project/constraints/'。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)

    # 在主路径 artifacts/project/constraints/ 写 1 个文件
    rule = repo / "artifacts" / "project" / "constraints" / "rule.md"
    rule.parent.mkdir(parents=True, exist_ok=True)
    rule.write_text("# 项目独有规则\n", encoding="utf-8")

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言主路径命中：含 "from artifacts/project/constraints/" + 文件数 ≥ 1
    assert "from artifacts/project/constraints/" in result.stderr, (
        f"stderr 缺少主路径日志：{result.stderr}"
    )
    # 断言 fallback=n/a（主路径命中）
    assert "fallback=n/a" in result.stderr, (
        f"主路径命中时应有 'fallback=n/a' 标记：{result.stderr}"
    )


def test_legacy_fallback_e2e(tmp_path):
    """TC-03：仅 legacy artifacts/{branch}/project/ 有文件 → stderr 含 fallback 主路径不存在提示。"""
    repo = tmp_path / "repo"
    repo.mkdir()
    _bootstrap_minimal_repo(repo)

    # 仅在 legacy 路径写文件（branch = main，由 _bootstrap_minimal_repo init）
    legacy = repo / "artifacts" / "main" / "project" / "experience" / "legacy-exp.md"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_text("# legacy 经验\n", encoding="utf-8")
    # 主路径 artifacts/project/experience/ 不存在

    result = _run_harness_install_check(repo)
    assert result.returncode == 0, f"stderr={result.stderr}\nstdout={result.stdout}"
    # 断言 legacy 命中：含 "from artifacts/main/project/experience/"
    assert "from artifacts/main/project/experience/" in result.stderr, (
        f"stderr 缺少 legacy fallback 日志：{result.stderr}"
    )
    # 断言 fallback=主路径 ... 不存在 提示
    assert "fallback=主路径" in result.stderr, (
        f"legacy fallback 时应有 'fallback=主路径' 提示：{result.stderr}"
    )
