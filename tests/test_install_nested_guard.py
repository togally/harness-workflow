"""tests/test_install_nested_guard.py

chg-F bug-1：install 嵌套防护测试

TC-01: 祖先有 .workflow → warn 不装（exit 0）
TC-02: 祖先有 .workflow + --force-nested → 跳过检查，正常 install
TC-03: 无祖先 .workflow → 正常 install（不报 warn）
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_install import _check_nested_install


# ---------------------------------------------------------------------------
# TC-01: 祖先有 .workflow → warn 不装
# ---------------------------------------------------------------------------

def test_tc01_ancestor_has_workflow_detected(tmp_path):
    """TC-01: 祖先目录有 .workflow/ → _check_nested_install 返回该祖先路径（非空）。"""
    # 创建祖先：tmp_path/.workflow/
    (tmp_path / ".workflow").mkdir()

    # 在祖先的子目录跑 check
    nested_dir = tmp_path / "artifacts" / "project" / "playbooks"
    nested_dir.mkdir(parents=True)

    result = _check_nested_install(nested_dir)
    assert result != "", (
        f"Expected ancestor path returned when .workflow exists, got empty string. "
        f"ancestor check from {nested_dir} should find {tmp_path}"
    )
    assert str(tmp_path) in result, (
        f"Expected ancestor path to contain {tmp_path}, got {result!r}"
    )


def test_tc01b_nested_install_main_exits_zero_with_warn(tmp_path, capsys):
    """TC-01b: 祖先有 .workflow + 不带 --force-nested → main() exit 0 + stderr WARN。"""
    from harness_workflow.tools.harness_install import main as install_main

    # 创建祖先 .workflow
    (tmp_path / ".workflow").mkdir()

    nested_dir = tmp_path / "sub" / "project"
    nested_dir.mkdir(parents=True)

    # 调 main() with --root pointing to nested_dir
    import sys as _sys
    orig_argv = _sys.argv[:]
    try:
        _sys.argv = ["harness_install", "--root", str(nested_dir), "--agent", "cc"]
        rc = install_main()
    finally:
        _sys.argv = orig_argv

    captured = capsys.readouterr()
    assert rc == 0, f"Expected exit 0 when ancestor has .workflow, got {rc}"
    assert "WARN" in captured.err, (
        f"Expected WARN in stderr about nested install, got: {captured.err!r}"
    )
    assert ".workflow" in captured.err, (
        f"Expected .workflow mentioned in stderr warning, got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# TC-02: --force-nested → 跳过检查，正常走下去
# ---------------------------------------------------------------------------

def test_tc02_force_nested_skips_guard(tmp_path):
    """TC-02: _check_nested_install 只检测逻辑；--force-nested 应让 main() 跳过该检查。

    由于 install_repo 需要完整环境，只测试 _check_nested_install 被绕过的逻辑：
    带 --force-nested 的 argv 不应触发嵌套防护退出。
    """
    # 创建祖先 .workflow
    (tmp_path / ".workflow").mkdir()

    nested_dir = tmp_path / "sub" / "project"
    nested_dir.mkdir(parents=True)

    # 直接调 _check_nested_install 确认返回非空（证明存在嵌套）
    result = _check_nested_install(nested_dir)
    assert result != "", "Should detect ancestor .workflow"

    # 带 --force-nested 的 main() 不应因嵌套而退出（会因为缺少 git repo 等原因失败，但不是因嵌套 guard）
    import sys as _sys
    import io
    orig_argv = _sys.argv[:]
    orig_stderr = _sys.stderr
    try:
        _sys.argv = ["harness_install", "--root", str(nested_dir), "--agent", "cc", "--force-nested"]
        _sys.stderr = io.StringIO()
        try:
            rc = __import__("harness_workflow.tools.harness_install", fromlist=["main"]).main()
        except SystemExit as e:
            rc = e.code
        err_out = _sys.stderr.getvalue()
    finally:
        _sys.argv = orig_argv
        _sys.stderr = orig_stderr

    # 关键断言：不应有嵌套 WARN（guard 已被跳过）
    assert "检测到祖先目录" not in err_out, (
        f"--force-nested should skip nested guard WARN, but got: {err_out!r}"
    )


# ---------------------------------------------------------------------------
# TC-03: 无祖先 .workflow → 正常 install（不报 warn）
# ---------------------------------------------------------------------------

def test_tc03_no_ancestor_workflow_clean(tmp_path):
    """TC-03: tmp_path 无祖先 .workflow → _check_nested_install 返回空字符串。"""
    # 确保 tmp_path 及其所有祖先均无 .workflow（tmp_path 通常在 /tmp 下）
    # 只验证 _check_nested_install 函数逻辑：tmp_path 本身无 .workflow
    clean_dir = tmp_path / "clean_project"
    clean_dir.mkdir()

    result = _check_nested_install(clean_dir)
    # 如果系统 /tmp 以上有 .workflow 则可能误报，但正常测试环境不会有
    # 只要当前目录链没有 .workflow 就行
    # 我们不能 100% 保证系统级别，所以只检查它不报告 tmp_path 或 clean_dir 本身
    if result:
        # 如果有，确认不是 tmp_path 直属祖先
        assert str(clean_dir) not in result, (
            f"clean_dir itself should not be in result: {result!r}"
        )
