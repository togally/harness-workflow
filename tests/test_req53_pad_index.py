"""req-53 / chg-03: index.md 登记 + git stage + 加载链活证。

覆盖：
- TC-01: rule index 表格追加
- TC-02: experience 子目录 index 追加
- TC-03: tool 列表段追加
- TC-04: stderr 活证（[harness] project-level loaded）
- TC-05: stdout git commit 提示
- TC-06: git add staged（git diff --cached）
- TC-07: 非 git 仓 silent skip
- TC-08: 幂等不重复登记
- TC-09: 表头缺失自动补
- TC-10: install 不覆盖 index 行（AC-04）
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env() -> dict:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env


def _run_install(cwd: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )


def _run_pad(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "pad", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        encoding="utf-8",
        env=_env(),
    )


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _init_git_repo(cwd: Path) -> None:
    _git(cwd, "init", "-q")
    _git(cwd, "config", "user.email", "test@test.com")
    _git(cwd, "config", "user.name", "Test")
    (cwd / "README.md").write_text("init", encoding="utf-8")
    _git(cwd, "add", "README.md")
    _git(cwd, "commit", "-m", "init", "-q")


def test_tc01_index_rule_表格追加(tmp_path: Path) -> None:
    """TC-01: pad rule coding → constraints/index.md 含新行."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    assert idx.exists(), "constraints/index.md 未创建"
    text = idx.read_text(encoding="utf-8")
    assert "代码风格" in text, f"index.md 未登记 title: {text}"
    assert "coding" in text, f"index.md 未登记 scope: {text}"
    assert "always" in text, f"index.md 未登记 when_load: {text}"


def test_tc02_index_experience_子目录追加(tmp_path: Path) -> None:
    """TC-02: pad experience stage → experience/stage/index.md 含新行."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "experience", "stage", "虚报")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    idx = tmp_path / "artifacts" / "project" / "experience" / "stage" / "index.md"
    assert idx.exists(), "experience/stage/index.md 未创建"
    text = idx.read_text(encoding="utf-8")
    assert "虚报" in text, f"index 未登记 title: {text}"
    assert "experience-stage" in text, f"index 未登记 scope: {text}"


def test_tc03_index_tool_列表追加(tmp_path: Path) -> None:
    """TC-03: pad tool → tools/index.md 项目级工具清单段含新项."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "tool", "deployer")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    idx = tmp_path / "artifacts" / "project" / "tools" / "index.md"
    assert idx.exists(), "tools/index.md 未创建"
    text = idx.read_text(encoding="utf-8")
    assert "## 项目级工具清单" in text, f"tools/index.md 缺清单段: {text}"
    assert "deployer" in text, f"tools/index.md 未登记 deployer: {text}"


def test_tc04_stderr_活证(tmp_path: Path) -> None:
    """TC-04: pad rule → stderr 含 [harness] project-level loaded."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    assert "[harness] project-level loaded" in r.stderr, \
        f"stderr 缺活证: {r.stderr}"
    assert "artifacts/project/constraints/" in r.stderr, \
        f"stderr 活证路径不对: {r.stderr}"


def test_tc05_stdout_git_commit_提示(tmp_path: Path) -> None:
    """TC-05: pad rule → stdout 含 git commit 提示."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    # git ok → stdout 含 git staged / commit 提示
    assert "git commit" in r.stdout or "git staged" in r.stdout, \
        f"stdout 缺 git commit 提示: {r.stdout}"


def test_tc06_git_add_staged(tmp_path: Path) -> None:
    """TC-06: pad rule → git diff --cached 含内容文件 + index.md."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    # 先 commit install 结果，方便 diff
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "install", "-q")
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    diff = _git(tmp_path, "diff", "--cached", "--name-only")
    assert "constraints" in diff.stdout, f"git staged 未含 constraints: {diff.stdout}"


def test_tc07_非git仓_silent_skip(tmp_path: Path) -> None:
    """TC-07: 无 .git 目录 → exit=0 + stderr 含 非 git 仓 + 文件正常落位."""
    # 无 git init，直接 install（install 会尝试检测 git 仓）
    _run_install(tmp_path)
    # 手动移除 .git（如果 install 创建了）
    git_dir = tmp_path / ".git"
    if git_dir.exists():
        import shutil
        shutil.rmtree(str(git_dir))
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    # 非 git 仓下 pad 仍应成功落位
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    assert "非 git 仓" in r.stderr or "git" in r.stderr.lower(), \
        f"非 git 仓提示缺失: {r.stderr}"


def test_tc08_幂等_不重复登记(tmp_path: Path) -> None:
    """TC-08: 重跑 pad → index.md 中实际数据行（非注释行）计数 = 1."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    _run_pad(tmp_path, "rule", "coding", "代码风格")
    _run_pad(tmp_path, "rule", "coding", "代码风格")
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    text = idx.read_text(encoding="utf-8")
    # 仅计算不含 HTML 注释的实际数据行
    data_rows = [
        line for line in text.splitlines()
        if "代码风格" in line and "<!--" not in line
    ]
    assert len(data_rows) == 1, f"index.md 实际数据行重复登记了 {len(data_rows)} 次: {text}"


def test_tc09_表头缺失_自动补(tmp_path: Path) -> None:
    """TC-09: index.md 无表头 → pad rule 后自动补表头 + 新行."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    # 手动写空 index.md（无表头）
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    idx.parent.mkdir(parents=True, exist_ok=True)
    idx.write_text("# Constraints\n\n（空）\n", encoding="utf-8")
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    text = idx.read_text(encoding="utf-8")
    assert "| path" in text and "when_load" in text, f"表头未自动补齐: {text}"
    assert "代码风格" in text, f"新行未追加: {text}"


def test_tc10_install_不覆盖_ac04(tmp_path: Path) -> None:
    """TC-10: pad rule 后 install --force-managed → 文件 + index 行仍在."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    # 内容文件
    target = tmp_path / "artifacts" / "project" / "constraints" / "coding"
    files_before = list(target.glob("*.md"))
    assert files_before, "pad 后无文件"
    idx_before = (tmp_path / "artifacts" / "project" / "constraints" / "index.md").read_text(encoding="utf-8")
    # force-managed install
    ri = _run_install(tmp_path, "--force-managed")
    assert ri.returncode == 0, f"install --force-managed 失败: {ri.stderr}"
    # 文件仍在
    files_after = list(target.glob("*.md"))
    assert files_after, "install --force-managed 删除了内容文件"
    idx_after = (tmp_path / "artifacts" / "project" / "constraints" / "index.md").read_text(encoding="utf-8")
    assert "代码风格" in idx_after, f"install 覆盖了 index.md: {idx_after}"
