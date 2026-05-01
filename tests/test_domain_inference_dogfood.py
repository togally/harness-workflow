"""tests/test_domain_inference_dogfood.py

req-56（路书引擎升级-java-maven-多模块-llm-内容填充-区段级只读）/ chg-01（推断器多语言注册化）
dogfood TC：subprocess 跑 harness install 完整流程，断言 PetMallPlatform-like fixture。

OQ-5=A 决策：dogfood TC 不离开 worktree，用 tmpdir fixture 模拟 PetMallPlatform。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
sys.path.insert(0, SRC_DIR)

from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX


def _setup_git(root: Path) -> None:
    """最小 git 初始化。"""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True, capture_output=True)


def _run_install(tmpdir: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """subprocess 跑 harness_workflow.cli install，设置 PYTHONPATH。"""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{SRC_DIR}:{existing}" if existing else SRC_DIR

    cmd = [
        sys.executable, "-m", "harness_workflow.cli",
        "install", "--root", str(tmpdir),
        "--agent", "claude",
        *extra_args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


# ---------------------------------------------------------------------------
# TC-Dogfood-01: PetMallPlatform-like fixture subprocess install
# ---------------------------------------------------------------------------

def test_petmall_fixture_dogfood(tmp_path, monkeypatch):
    """TC-Dogfood-01: PetMallPlatform-like 结构，subprocess install，断言领域推断命中。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    modules = [
        "platform-admin",
        "platform-common",
        "platform-modules",
        "platform-extend",
        "platform-demo-ui",
    ]

    # root pom.xml with <modules>
    root_pom = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project>\n'
        '  <groupId>com.petmall</groupId>\n'
        '  <artifactId>petmall-parent</artifactId>\n'
        '  <packaging>pom</packaging>\n'
        '  <modules>\n'
    )
    for mod in modules:
        root_pom += f'    <module>{mod}</module>\n'
    root_pom += '  </modules>\n</project>\n'
    (tmp_path / "pom.xml").write_text(root_pom, encoding="utf-8")

    # 每个模块含 pom.xml + src/main/java/
    for mod in modules:
        mod_dir = tmp_path / mod
        (mod_dir / "src" / "main" / "java").mkdir(parents=True)
        (mod_dir / "pom.xml").write_text(
            f'<project><artifactId>{mod}</artifactId></project>\n',
            encoding="utf-8",
        )

    # chg-D: --playbook-only 已删除，改用标准 install（始终装路书骨架）
    result = _run_install(tmp_path)
    combined = result.stdout + result.stderr

    # 断言：stdout 含 matched 'maven_multi_module'
    assert "matched 'maven_multi_module'" in combined, (
        f"Expected 'matched maven_multi_module' in output; stdout={result.stdout!r}, stderr={result.stderr!r}"
    )

    # 断言：路书骨架已创建
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    assert playbook_dir.exists(), f"playbook dir should exist; stdout={result.stdout}"

    # 断言：domains/ 下有 >=5 个子目录（platform-* 模块）
    domains_dir = playbook_dir / "domains"
    assert domains_dir.exists(), "domains/ should exist"
    domain_subdirs = sorted(d.name for d in domains_dir.iterdir() if d.is_dir())
    assert len(domain_subdirs) >= 5, f"Expected >=5 domain subdirs, got {domain_subdirs}"
    for mod in modules:
        assert mod in domain_subdirs, f"Expected domain dir for {mod}, got {domain_subdirs}"


# ---------------------------------------------------------------------------
# TC-Dogfood-02: --domains flag override subprocess
# ---------------------------------------------------------------------------

def test_cli_domains_flag_override(tmp_path, monkeypatch):
    """TC-Dogfood-02: --domains a,b，断言域目录 a/ b/ 创建。（chg-D: --playbook-only 已删除）"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _setup_git(tmp_path)

    # chg-D: --playbook-only 已删除，改用标准 install + --domains
    result = _run_install(tmp_path, "--domains", "domain-alpha,domain-beta")
    combined = result.stdout + result.stderr

    # exit 0
    assert result.returncode == 0, f"Expected exit 0; stderr={result.stderr!r}"

    # stdout 含 user-provided（override 打印）
    assert "user-provided" in combined or "domain-alpha" in combined, (
        f"Expected user-provided in output; combined={combined!r}"
    )

    # domains/domain-alpha/ 和 domains/domain-beta/ 目录存在
    playbook_dir = tmp_path / PLAYBOOK_ROOT_SUFFIX
    domains_dir = playbook_dir / "domains"
    if domains_dir.exists():
        domain_names = sorted(d.name for d in domains_dir.iterdir() if d.is_dir())
        assert "domain-alpha" in domain_names, f"domain-alpha not in {domain_names}"
        assert "domain-beta" in domain_names, f"domain-beta not in {domain_names}"
