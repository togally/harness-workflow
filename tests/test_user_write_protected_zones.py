"""bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）/
chg-04（硬门禁 --contract user-write-protected-zones + dev-mode 三层探测）dogfood 测试用例。

覆盖范围：
- TC-04a：user project 手写 .workflow/context/roles/my-custom-role.md → ABORT exit 1
- TC-04b：本仓（dev mode：pyproject name = "harness-workflow"）→ silent skip exit 0
- TC-04c：工具产出区文件（flow/requirements/req-99/...）→ silent skip
- TC-04d：三层 dev-mode 探测分别命中均触发豁免
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.validate_contract import (  # noqa: E402
    _is_dev_repo,
    check_user_write_protected_zones,
)


# ─────────────────────────────────────────────
# _is_dev_repo 三层探测单元测试（TC-04d）
# ─────────────────────────────────────────────

def test_tc04d_is_dev_repo_layer1_pyproject(tmp_path: Path) -> None:
    """TC-04d Layer 1：pyproject.toml::name = 'harness-workflow' → dev mode。"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "harness-workflow"\nversion = "0.1.0"\n', encoding="utf-8")
    assert _is_dev_repo(tmp_path) is True, "pyproject name=harness-workflow should trigger dev mode"


def test_tc04d_is_dev_repo_layer2_src_dir(tmp_path: Path) -> None:
    """TC-04d Layer 2：src/harness_workflow/ 目录存在 → dev mode。"""
    src_dir = tmp_path / "src" / "harness_workflow"
    src_dir.mkdir(parents=True, exist_ok=True)
    assert _is_dev_repo(tmp_path) is True, "src/harness_workflow/ directory should trigger dev mode"


def test_tc04d_is_dev_repo_layer3_env(tmp_path: Path, monkeypatch) -> None:
    """TC-04d Layer 3：HARNESS_DEV_REPO_ROOT env 与 root 一致 → dev mode。"""
    monkeypatch.setenv("HARNESS_DEV_REPO_ROOT", str(tmp_path.resolve()))
    assert _is_dev_repo(tmp_path) is True, "HARNESS_DEV_REPO_ROOT matching root should trigger dev mode"


def test_tc04d_is_dev_repo_user_project(tmp_path: Path, monkeypatch) -> None:
    """TC-04d user project：全否 → False。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    # tmp_path: no pyproject.toml, no src/harness_workflow, no env
    assert _is_dev_repo(tmp_path) is False, "plain tmpdir should NOT be dev mode"


def test_tc04d_is_dev_repo_current_repo() -> None:
    """TC-04d：本仓自身（pyproject.toml + src/）命中 dev mode。"""
    assert _is_dev_repo(REPO_ROOT) is True, "harness-workflow repo root should be dev mode"


# ─────────────────────────────────────────────
# TC-04a：user project 手写野文件 → ABORT exit 1
# ─────────────────────────────────────────────

def test_tc04a_user_project_violation(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-04a：tmpdir 无 pyproject.toml / src/harness_workflow / env，
    手写 .workflow/context/roles/my-custom-role.md → check_user_write_protected_zones exit 1。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 创建野文件
    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom-role.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# My Custom Role\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1, (
        f"check_user_write_protected_zones should return 1 for wild file; got rc={rc}"
    )
    assert "violation" in captured.err, (
        f"Expected 'violation' in stderr; got:\n{captured.err!r}"
    )
    assert ".workflow/context/roles/my-custom-role.md" in captured.err, (
        f"Expected wild file path in stderr violation list; got:\n{captured.err!r}"
    )


def test_tc04a_user_project_violation_subprocess(tmp_path: Path, monkeypatch) -> None:
    """TC-04a subprocess 变体：CLI 子进程 harness validate --contract user-write-protected-zones
    在含野文件的 user project 中返回 exit 1。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom-role.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# My Custom Role\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "user-write-protected-zones", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, (
        f"Expected exit code 1 for wild file in user project; "
        f"got {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"
    )
    assert "violation" in result.stderr, (
        f"Expected 'violation' in subprocess stderr; got:\n{result.stderr!r}"
    )


# ─────────────────────────────────────────────
# TC-04b：dev mode（本仓）→ silent skip exit 0
# ─────────────────────────────────────────────

def test_tc04b_dev_mode_silent_skip(capsys) -> None:
    """TC-04b：本仓（pyproject.toml + src/harness_workflow/）→ silent skip exit 0。"""
    rc = check_user_write_protected_zones(REPO_ROOT)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"check_user_write_protected_zones should return 0 for dev mode repo; got rc={rc}\n"
        f"stderr:\n{captured.err!r}"
    )
    # dev mode 时不应输出 violation
    assert "violation" not in captured.err, (
        f"Dev mode should not produce violation output; got:\n{captured.err!r}"
    )


def test_tc04b_dev_mode_subprocess() -> None:
    """TC-04b subprocess 变体：harness validate --contract user-write-protected-zones 在本仓 exit 0。"""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "user-write-protected-zones", "--root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 for dev mode repo; got {result.returncode}\n"
        f"stdout:{result.stdout}\nstderr:{result.stderr}"
    )


# ─────────────────────────────────────────────
# TC-04c：工具产出区文件 → silent skip
# ─────────────────────────────────────────────

def test_tc04c_tool_output_zone_skip(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-04c：tmpdir 含工具产出区文件（flow/requirements/req-99/requirement.md），
    check_user_write_protected_zones → silent skip exit 0。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 工具产出区文件（flow/requirements 在白名单中）
    tool_file = tmp_path / ".workflow" / "flow" / "requirements" / "req-99-test" / "requirement.md"
    tool_file.parent.mkdir(parents=True, exist_ok=True)
    tool_file.write_text("# req-99 requirement\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"Tool output zone file should not trigger violation; got rc={rc}\nstderr:\n{captured.err!r}"
    )
    assert "violation" not in captured.err, (
        f"Tool output zone should produce no violation output; got:\n{captured.err!r}"
    )
