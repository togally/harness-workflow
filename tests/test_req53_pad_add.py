"""req-53 / chg-02: _pad_add 真实落位 + 三份模板 + 幂等。

覆盖：
- TC-01: rule coding 落位 + frontmatter
- TC-02: experience stage 落位
- TC-03: tool 不分 scope 落位
- TC-04: frontmatter 字段完整（6 字段）
- TC-05: write_if_missing 幂等（重跑不覆盖）
- TC-06: 非法 kind 不落位
- TC-07: tool frontmatter tool_id
- TC-08: 三类 pad dogfood（fresh repo）
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


def _run_install(cwd: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    assert result.returncode == 0, f"install failed: {result.stderr}"


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


def test_tc01_add_rule_coding_落位(tmp_path: Path) -> None:
    """TC-01: pad rule coding 文件落位 + 含 kind/scope/内容段."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "禁止-API-硬编码")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    # 文件应存在
    target = tmp_path / "artifacts" / "project" / "constraints" / "coding" / "禁止-api-硬编码.md"
    assert target.exists(), f"文件未落位: {target}"
    content = target.read_text(encoding="utf-8")
    assert "kind: rule" in content, f"frontmatter 缺 kind: rule: {content}"
    assert "scope: coding" in content, f"frontmatter 缺 scope: coding: {content}"
    assert "## 内容" in content, f"模板缺 ## 内容段: {content}"


def test_tc02_add_experience_stage_落位(tmp_path: Path) -> None:
    """TC-02: pad experience stage 文件落位."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "experience", "stage", "虚报教训")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    target = tmp_path / "artifacts" / "project" / "experience" / "stage" / "虚报教训.md"
    assert target.exists(), f"文件未落位: {target}"
    content = target.read_text(encoding="utf-8")
    assert "kind: experience" in content
    assert "scope: stage" in content


def test_tc03_add_tool_不分scope_落位(tmp_path: Path) -> None:
    """TC-03: pad tool petmall-deployer 落位."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "tool", "petmall-deployer")
    assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
    target = tmp_path / "artifacts" / "project" / "tools" / "petmall-deployer.md"
    assert target.exists(), f"文件未落位: {target}"
    content = target.read_text(encoding="utf-8")
    assert "scope: tools" in content


def test_tc04_add_frontmatter_字段完整(tmp_path: Path) -> None:
    """TC-04: frontmatter 含 6 字段：id/kind/scope/title/created_at/when_load."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "rule", "coding", "代码风格")
    assert r.returncode == 0
    # 找文件（slug 可能是中文原名或转义）
    constraint_dir = tmp_path / "artifacts" / "project" / "constraints" / "coding"
    files = list(constraint_dir.glob("*.md"))
    assert files, f"constraints/coding/ 下无文件: {list(constraint_dir.iterdir())}"
    content = files[0].read_text(encoding="utf-8")
    for field in ["id:", "kind:", "scope:", "title:", "created_at:", "when_load: always"]:
        assert field in content, f"frontmatter 缺字段 {field}: {content}"


def test_tc05_add_write_if_missing_幂等(tmp_path: Path) -> None:
    """TC-05: 重跑同命令 → exit=0 + stderr 含"已存在，跳过"."""
    _run_install(tmp_path)
    _run_pad(tmp_path, "rule", "coding", "禁止-API-硬编码")
    r2 = _run_pad(tmp_path, "rule", "coding", "禁止-API-硬编码")
    assert r2.returncode == 0, f"幂等失败 stdout={r2.stdout}\nstderr={r2.stderr}"
    assert "已存在，跳过" in r2.stderr, f"缺幂等提示: {r2.stderr}"


def test_tc06_add_illegal_kind_不落位(tmp_path: Path) -> None:
    """TC-06: 非法 kind → exit≠0 + 文件不创建."""
    r = _run_pad(tmp_path, "foo", "bar", "baz")
    assert r.returncode != 0
    bogus = tmp_path / "artifacts" / "project"
    # 无文件创建
    for f in bogus.rglob("*.md") if bogus.exists() else []:
        assert False, f"非法 kind 不应创建任何文件: {f}"


def test_tc07_add_tool_frontmatter_tool_id(tmp_path: Path) -> None:
    """TC-07: tool frontmatter 含 tool_id + keywords."""
    _run_install(tmp_path)
    r = _run_pad(tmp_path, "tool", "petmall-deployer")
    assert r.returncode == 0
    target = tmp_path / "artifacts" / "project" / "tools" / "petmall-deployer.md"
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "tool_id:" in content, f"缺 tool_id: {content}"
    assert "keywords:" in content, f"缺 keywords: {content}"


def test_tc08_dogfood_add_fresh_repo_三类(tmp_path: Path) -> None:
    """TC-08: fresh repo → 3 条 pad（rule/experience/tool）文件全落位 + install --check 不报错."""
    _run_install(tmp_path)
    r1 = _run_pad(tmp_path, "rule", "coding", "禁止硬编码")
    assert r1.returncode == 0, f"stdout={r1.stdout}\nstderr={r1.stderr}"
    r2 = _run_pad(tmp_path, "experience", "stage", "虚报教训")
    assert r2.returncode == 0, f"stdout={r2.stdout}\nstderr={r2.stderr}"
    r3 = _run_pad(tmp_path, "tool", "deployer")
    assert r3.returncode == 0, f"stdout={r3.stdout}\nstderr={r3.stderr}"
    # 三文件存在
    assert (tmp_path / "artifacts" / "project" / "tools" / "deployer.md").exists()
    assert (tmp_path / "artifacts" / "project" / "experience" / "stage").exists()
    assert (tmp_path / "artifacts" / "project" / "constraints" / "coding").exists()
    # install --check 不报错
    rc = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", "--check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        env=_env(),
    )
    assert rc.returncode == 0, f"install --check 报错: {rc.stderr}"
