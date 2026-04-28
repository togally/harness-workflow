"""TC-04 / TC-05：archive 前置 revert dry-run 测试用例。

req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地
sug-31（done 后 commit + revert dry-run 自动化）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _init_git_repo(tmp_path: Path) -> None:
    """在 tmp_path 下初始化一个干净的 git repo 并创建初始 commit。"""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True, check=True)
    # 创建初始 commit
    (tmp_path / "README.md").write_text("initial", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True, check=True)


def test_tc04_revert_dry_run_no_conflict(tmp_path: Path) -> None:
    """TC-04：干净 commit → dry-run 无冲突 → exit 0。"""
    _init_git_repo(tmp_path)

    from harness_workflow.workflow_helpers import _revert_dry_run_self_check
    rc = _revert_dry_run_self_check(tmp_path, "req-test")
    assert rc == 0, f"Expected exit 0 (no conflict), got {rc}"


def test_tc04_skip_revert_check(tmp_path: Path) -> None:
    """TC-04 变体：skip_check=True → 无论是否冲突都 exit 0。"""
    _init_git_repo(tmp_path)

    from harness_workflow.workflow_helpers import _revert_dry_run_self_check
    rc = _revert_dry_run_self_check(tmp_path, "req-test", skip_check=True)
    assert rc == 0


def test_tc05_cli_archive_help_has_skip_flag() -> None:
    """TC-05 前置：CLI archive --help 含 --skip-revert-check 选项。"""
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "archive", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    help_text = result.stdout + result.stderr
    assert "skip-revert-check" in help_text, (
        f"Expected --skip-revert-check in archive --help, got:\n{help_text}"
    )


def test_revert_dry_run_no_git_repo(tmp_path: Path) -> None:
    """非 git 仓库时，helper 不崩溃 + exit 0（跳过检查）。"""
    from harness_workflow.workflow_helpers import _revert_dry_run_self_check
    rc = _revert_dry_run_self_check(tmp_path, "req-test")
    assert rc == 0


def test_revert_dry_run_no_commits(tmp_path: Path) -> None:
    """git init 但无 commit → helper 不崩溃 + exit 0。"""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, capture_output=True, check=True)

    from harness_workflow.workflow_helpers import _revert_dry_run_self_check
    rc = _revert_dry_run_self_check(tmp_path, "req-test")
    assert rc == 0
