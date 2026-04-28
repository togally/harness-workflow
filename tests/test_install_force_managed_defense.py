"""bugfix-8（用户项目区与开发期区分离 + 反向清理盲区修复 + 用户写保护硬门禁）/
chg-03（--force-managed 透传防御 + 实证测试）dogfood 测试用例。

覆盖范围：
- TC-03a：install_repo 入口 stderr 含 "[install_repo] force_managed received: True/False"
- TC-03b：force_managed=False 时 skip 分支输出 "skipping user-modified"
- TC-03c：force_managed=True 时 skip 分支不输出 "skipping user-modified"
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stderr
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    MANAGED_STATE_PATH,
    _managed_hash,
    _sync_requirement_workflow_managed_files,
    _sync_scaffold_v2_mirror_to_live,
    install_repo,
)


def _git_init(root: Path) -> None:
    """最小 git 初始化。"""
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def test_tc03a_install_repo_force_managed_stderr(tmp_path: Path, monkeypatch) -> None:
    """TC-03a：install_repo 入口 stderr 含 '[install_repo] force_managed received: True/False'。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    stderr_buf = io.StringIO()
    with redirect_stderr(stderr_buf):
        rc = install_repo(tmp_path, force_skill=True, check=False, force_managed=False)
    stderr_out = stderr_buf.getvalue()

    assert "[install_repo] force_managed received: False" in stderr_out, (
        f"Expected '[install_repo] force_managed received: False' in stderr; got:\n{stderr_out!r}"
    )


def test_tc03a_install_repo_force_managed_true_stderr(tmp_path: Path, monkeypatch) -> None:
    """TC-03a True 变体：force_managed=True 时 stderr 含 '[install_repo] force_managed received: True'。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    stderr_buf = io.StringIO()
    with redirect_stderr(stderr_buf):
        rc = install_repo(tmp_path, force_skill=True, check=False, force_managed=True)
    stderr_out = stderr_buf.getvalue()

    assert "[install_repo] force_managed received: True" in stderr_out, (
        f"Expected '[install_repo] force_managed received: True' in stderr; got:\n{stderr_out!r}"
    )


def _setup_mirror_modified_file(tmp_path: Path) -> tuple[str, str, str]:
    """Helper：在 tmpdir 中设置一个已被用户修改的 mirror 文件（current != expected，但 managed_state
    登记的 hash 是原始 mirror 内容 hash，表示"曾是 managed 但被用户改过了"）。

    返回 (target_rel, original_content, modified_content)。
    跳过条件：mirror 为空 or 全为白名单。
    """
    from harness_workflow.workflow_helpers import (
        _scaffold_v2_file_contents,
        _SCAFFOLD_V2_MIRROR_WHITELIST,
    )

    mirror = _scaffold_v2_file_contents(tmp_path, include_agents=False, include_claude=False, language="cn")
    if not mirror:
        pytest.skip("mirror is empty, cannot test skip branch")

    target_rel = None
    for rel in sorted(mirror):
        if not any(w in rel for w in _SCAFFOLD_V2_MIRROR_WHITELIST):
            target_rel = rel
            break
    if target_rel is None:
        pytest.skip("no non-whitelisted file in mirror")

    original_content = mirror[target_rel]
    modified_content = original_content + "\n# user-modified\n"

    target_path = tmp_path / target_rel
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(modified_content, encoding="utf-8")

    # 登记 managed-files.json：hash 为原始 mirror 内容（模拟"工具写入后被用户改"）
    # managed_state[relative] = hash(original) != hash(modified) 且 current != expected
    # → 走 branch 5/6（skip 或 overwrite）
    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps(
            {"tool_version": "0.2.0", "managed_files": {target_rel: _managed_hash(original_content)}},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )

    return target_rel, original_content, modified_content


def test_tc03b_sync_mirror_force_managed_false_skips(tmp_path: Path) -> None:
    """TC-03b：_sync_scaffold_v2_mirror_to_live：force_managed=False 时，
    用户改过的文件 actions 含 'skipped user-modified (mirror)'。

    设置：managed_state[target] = hash(original) 但 live 文件内容为 modified（≠ original）
    → current_hash ≠ managed_state[target] → branch 5（skip）。
    """
    target_rel, _orig, _mod = _setup_mirror_modified_file(tmp_path)

    actions = _sync_scaffold_v2_mirror_to_live(tmp_path, check=False, force_managed=False)
    action_str = " ".join(actions)
    assert "skipped user-modified (mirror)" in action_str, (
        f"Expected 'skipped user-modified (mirror)' in actions when force_managed=False; got: {actions}"
    )


def test_tc03c_sync_mirror_force_managed_true_no_skip(tmp_path: Path) -> None:
    """TC-03c：_sync_scaffold_v2_mirror_to_live：force_managed=True 时，
    用户改过的文件 actions 不含 'skipped user-modified'，含 'overwrote user-modified (mirror)'。
    """
    target_rel, _orig, _mod = _setup_mirror_modified_file(tmp_path)

    stderr_buf = io.StringIO()
    with redirect_stderr(stderr_buf):
        actions = _sync_scaffold_v2_mirror_to_live(tmp_path, check=False, force_managed=True)

    action_str = " ".join(actions)
    stderr_out = stderr_buf.getvalue()

    # force_managed=True 时不应出现 "skipped user-modified"
    assert "skipped user-modified" not in action_str, (
        f"force_managed=True should NOT produce 'skipped user-modified' actions; got: {actions}"
    )
    assert "skipping user-modified" not in stderr_out, (
        f"force_managed=True should NOT produce 'skipping user-modified' stderr; got:\n{stderr_out!r}"
    )
    # 应出现 "overwrote user-modified (mirror)"
    assert "overwrote user-modified (mirror)" in action_str, (
        f"force_managed=True should produce 'overwrote user-modified (mirror)' action; got: {actions}"
    )
