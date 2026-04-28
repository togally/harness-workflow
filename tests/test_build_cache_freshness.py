"""bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）/
chg-05（lint：扫 build/ 残留）dogfood 测试用例。

覆盖范围：
- TC-05a：tmpdir 模拟 build/lib/.../scaffold_v2/ 含 src/ 已删 usage-reporter.md
  → check_build_cache_freshness exit 1 + stderr 含 WARNING + hint
- TC-05b：tmpdir 无 build/ → exit 0 silent skip
- TC-05c：dev mode（本仓 chg-01 已清理 build/）→ 本仓 build/ lint 全绿
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.validate_contract import check_build_cache_freshness  # noqa: E402


# ─────────────────────────────────────────────
# TC-05a：tmpdir build/ 含已删文件 → WARNING + hint
# ─────────────────────────────────────────────

def test_tc05a_stale_build_file_triggers_warning(tmp_path: Path, capsys) -> None:
    """TC-05a：tmpdir 模拟 build/lib/harness_workflow/assets/scaffold_v2/ 含
    src/ 已删的 '.workflow/context/roles/usage-reporter.md'
    → check_build_cache_freshness exit 1 + stderr 含 WARNING + hint。
    """
    # 构建 src scaffold（不含 usage-reporter.md）
    src_scaffold = tmp_path / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    src_scaffold.mkdir(parents=True, exist_ok=True)
    # 放一个正常文件在 src
    normal_file = src_scaffold / ".workflow" / "context" / "roles" / "base-role.md"
    normal_file.parent.mkdir(parents=True, exist_ok=True)
    normal_file.write_text("# base-role\n", encoding="utf-8")

    # 构建 build scaffold（含 stale usage-reporter.md）
    build_scaffold = tmp_path / "build" / "lib" / "harness_workflow" / "assets" / "scaffold_v2"
    build_scaffold.mkdir(parents=True, exist_ok=True)
    # 同步 normal 文件
    build_normal = build_scaffold / ".workflow" / "context" / "roles" / "base-role.md"
    build_normal.parent.mkdir(parents=True, exist_ok=True)
    build_normal.write_text("# base-role\n", encoding="utf-8")
    # 加 stale 文件（src 已删，build 残留）
    stale_file = build_scaffold / ".workflow" / "context" / "roles" / "usage-reporter.md"
    stale_file.parent.mkdir(parents=True, exist_ok=True)
    stale_file.write_text("# usage-reporter（stale）\n", encoding="utf-8")

    rc = check_build_cache_freshness(tmp_path)
    captured = capsys.readouterr()

    assert rc == 1, (
        f"check_build_cache_freshness should return 1 (WARNING) for stale file; got rc={rc}"
    )
    assert "WARNING" in captured.err, (
        f"Expected WARNING in stderr; got:\n{captured.err!r}"
    )
    assert "usage-reporter.md" in captured.err, (
        f"Expected stale file name in stderr; got:\n{captured.err!r}"
    )
    assert "rm -rf build/" in captured.err, (
        f"Expected hint 'rm -rf build/' in stderr; got:\n{captured.err!r}"
    )


def test_tc05a_stale_subprocess(tmp_path: Path) -> None:
    """TC-05a subprocess 变体：CLI 子进程返回 exit 1 + stderr 含 WARNING。"""
    src_scaffold = tmp_path / "src" / "harness_workflow" / "assets" / "scaffold_v2"
    src_scaffold.mkdir(parents=True, exist_ok=True)
    normal = src_scaffold / ".workflow" / "context" / "roles" / "base-role.md"
    normal.parent.mkdir(parents=True, exist_ok=True)
    normal.write_text("# base-role\n", encoding="utf-8")

    build_scaffold = tmp_path / "build" / "lib" / "harness_workflow" / "assets" / "scaffold_v2"
    build_scaffold.mkdir(parents=True, exist_ok=True)
    build_normal = build_scaffold / ".workflow" / "context" / "roles" / "base-role.md"
    build_normal.parent.mkdir(parents=True, exist_ok=True)
    build_normal.write_text("# base-role\n", encoding="utf-8")
    stale = build_scaffold / ".workflow" / "context" / "roles" / "usage-reporter.md"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("# stale\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "build-cache-freshness", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, (
        f"Expected exit 1; got {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"
    )
    assert "WARNING" in result.stderr, (
        f"Expected WARNING in subprocess stderr; got:\n{result.stderr!r}"
    )


# ─────────────────────────────────────────────
# TC-05b：无 build/ → silent skip exit 0
# ─────────────────────────────────────────────

def test_tc05b_no_build_dir_silent_skip(tmp_path: Path, capsys) -> None:
    """TC-05b：tmpdir 无 build/ 目录 → check_build_cache_freshness exit 0 silent skip。"""
    rc = check_build_cache_freshness(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"check_build_cache_freshness should return 0 when no build/ dir; got rc={rc}"
    )
    assert "WARNING" not in captured.err, (
        f"No WARNING expected when build/ absent; got stderr:\n{captured.err!r}"
    )


def test_tc05b_no_build_subprocess(tmp_path: Path) -> None:
    """TC-05b subprocess 变体：无 build/ 时 CLI exit 0。"""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "build-cache-freshness", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with no build/; got {result.returncode}\n"
        f"stdout:{result.stdout}\nstderr:{result.stderr}"
    )


# ─────────────────────────────────────────────
# TC-05c / AC-05-d：本仓自审 build-cache-freshness 全绿（chg-01 已清 build/）
# ─────────────────────────────────────────────

def test_tc05c_current_repo_build_freshness(capsys) -> None:
    """TC-05c / AC-05-d：本仓自审 harness validate --contract build-cache-freshness
    在 chg-01 清理 build/ 后应 PASS（exit 0 or 1 with 0 stale usage-reporter.md）。
    """
    rc = check_build_cache_freshness(REPO_ROOT)
    captured = capsys.readouterr()

    # 关键断言：usage-reporter.md 不在 stale 列表中（chg-01 已清理）
    assert "usage-reporter.md" not in captured.err, (
        f"usage-reporter.md should have been cleaned in chg-01; still in build-cache-freshness:\n{captured.err!r}"
    )
