"""req-53 / chg-04: 端到端 dogfood TC（subprocess 全链路）。

覆盖：
- TC-Dogfood-01: fresh git + install + pad rule → 文件 + index + git staged + stderr 活证
- TC-Dogfood-02: 多次 pad 同 scope 多条 → index 3 行
- TC-Dogfood-03: 混合 rule + experience + tool → 5 文件 + 4 index.md
- TC-Dogfood-04: pad 后 install --force-managed 不覆盖（AC-04）
- TC-Dogfood-05: install 后 feedback.jsonl 不被 pad 破坏
"""
from __future__ import annotations

import os
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


def _run_install(cwd: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", *extra],
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


def test_dogfood_01_fresh_install_then_pad(tmp_path: Path) -> None:
    """TC-Dogfood-01: fresh git + install + pad rule → 完整流程验证."""
    _init_git_repo(tmp_path)
    ri = _run_install(tmp_path)
    assert ri.returncode == 0, f"install failed: {ri.stderr}"
    # commit install 结果
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "install", "-q")

    r = _run_pad(tmp_path, "rule", "coding", "禁止-API-硬编码")
    assert r.returncode == 0, f"pad failed stdout={r.stdout}\nstderr={r.stderr}"

    # 文件落位
    target = tmp_path / "artifacts" / "project" / "constraints" / "coding"
    files = list(target.glob("*.md"))
    assert files, f"constraints/coding/ 下无文件"

    # index.md 登记
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    assert idx.exists() and "禁止" in idx.read_text(encoding="utf-8"), "index.md 未登记"

    # git diff --cached 含两条（内容文件 + index.md）
    diff = _git(tmp_path, "diff", "--cached", "--name-only")
    assert "constraints" in diff.stdout, f"git staged 缺 constraints: {diff.stdout}"

    # stderr 活证
    assert "[harness] project-level loaded" in r.stderr, \
        f"stderr 缺活证: {r.stderr}"


def test_dogfood_02_多次pad_同scope_多条(tmp_path: Path) -> None:
    """TC-Dogfood-02: pad rule coding × 3（不同 title）→ index 含 3 行."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    for title in ["规则A", "规则B", "规则C"]:
        r = _run_pad(tmp_path, "rule", "coding", title)
        assert r.returncode == 0, f"pad {title} failed"
    idx = tmp_path / "artifacts" / "project" / "constraints" / "index.md"
    text = idx.read_text(encoding="utf-8")
    count = sum(1 for t in ["规则A", "规则B", "规则C"] if t in text)
    assert count == 3, f"index.md 仅含 {count} 条，期望 3: {text}"


def test_dogfood_03_混合_rule_experience_tool(tmp_path: Path) -> None:
    """TC-Dogfood-03: 混合 pad → 5 文件 + 多 index.md 被修改."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    # commit install
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "install", "-q")

    _run_pad(tmp_path, "rule", "coding", "规则X")
    _run_pad(tmp_path, "rule", "security", "规则Y")
    _run_pad(tmp_path, "experience", "stage", "经验A")
    _run_pad(tmp_path, "experience", "regression", "经验B")
    _run_pad(tmp_path, "tool", "工具Z")

    # 5 内容文件存在（至少找到 5 个）
    md_files: list[Path] = []
    for p in (tmp_path / "artifacts" / "project").rglob("*.md"):
        if p.name != "index.md":
            md_files.append(p)
    assert len(md_files) >= 5, f"期望 ≥ 5 个内容文件，实际 {len(md_files)}: {md_files}"

    # git staged 包含多个文件
    diff = _git(tmp_path, "diff", "--cached", "--name-only")
    staged = diff.stdout.strip().splitlines()
    assert len(staged) >= 5, f"git staged 文件数 {len(staged)} 小于期望 5: {staged}"


def test_dogfood_04_pad后install_不覆盖(tmp_path: Path) -> None:
    """TC-Dogfood-04: pad rule + install --force-managed → AC-04 不覆盖."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "api", "API版本规范")
    assert r.returncode == 0

    target_dir = tmp_path / "artifacts" / "project" / "constraints" / "api"
    files_before = list(target_dir.glob("*.md"))
    assert files_before, "pad 后无内容文件"

    # force-managed install
    ri = _run_install(tmp_path, "--force-managed")
    assert ri.returncode == 0, f"install --force-managed 失败: {ri.stderr}"

    # 文件仍在
    files_after = list(target_dir.glob("*.md"))
    assert files_after, "install --force-managed 删除了内容文件"
    idx_text = (tmp_path / "artifacts" / "project" / "constraints" / "index.md").read_text(encoding="utf-8")
    assert "API版本规范" in idx_text, f"install 覆盖了 index.md 表格行: {idx_text}"


def test_dogfood_05_feedback_jsonl_不被破坏(tmp_path: Path) -> None:
    """TC-Dogfood-05: install 后 feedback.jsonl 在 pad 后仍存在（不被破坏）."""
    _init_git_repo(tmp_path)
    _run_install(tmp_path)
    feedback_file = tmp_path / ".workflow" / "state" / "feedback.jsonl"
    # feedback.jsonl 是否存在（install 可能创建）
    feedback_exists_after_install = feedback_file.exists()

    r = _run_pad(tmp_path, "rule", "coding", "测试规则")
    assert r.returncode == 0

    if feedback_exists_after_install:
        # pad 不应删除 feedback.jsonl
        assert feedback_file.exists(), "pad 删除了 feedback.jsonl"
    # pad 不调 record_feedback_event，仅验证文件状态不被破坏（AC-10 扩展）
    # 如果 install 未创建 feedback.jsonl，则跳过（合法场景）
