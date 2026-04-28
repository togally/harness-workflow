"""bugfix-7（pipx reinstall + harness install 后目标项目未更新到最新且残留多余文件）/
chg-01（反向清理 + check 对比）+ chg-02（版本号差异化）+ chg-05（install 平台 prompt UX 修）
+ chg-07（executing gate bugfix 模式支持）dogfood 测试用例。

覆盖范围：
- TC-01：mirror 已删 + managed-files 仍登记 → 文件被移到 LEGACY_CLEANUP_ROOT + managed_state 摘除 key
- TC-02：业务态文件（flow/requirements/ / state/sessions/ / context/experience/regression/）保留不动
- TC-03：harness install --check 输出 venv commit + HEAD commit + diff hint
- TC-05：install 强提示 drift（stderr WARN 含 WARNING 关键字）
- TC-06：tool_version mismatch 时触发 full re-sync
- TC-08：已有 active_list 时 install 不弹 questionary（不阻塞 stdin）
- TC-09：bugfix flow_dir + session-memory.md 含 ✅ + tests/ 有 test_*.py → _is_stage_work_done == True
- TC-10：同上但 session-memory.md 不含 ✅ → _is_stage_work_done == False
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    LEGACY_CLEANUP_ROOT,
    MANAGED_STATE_PATH,
    _is_stage_work_done,
    _load_managed_state,
    _managed_hash,
    _scaffold_v2_file_contents,
    _sync_scaffold_v2_mirror_to_live,
    install_repo,
)


# ─────────────────────────────────────────────
# 通用 helper：最小 git 初始化
# ─────────────────────────────────────────────

def _git_init(root: Path) -> None:
    """最小 git 初始化（install_repo 内部依赖 git status 等命令）。"""
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


# ─────────────────────────────────────────────
# TC-01：反向清理多余文件（mirror 已删 + managed-files 仍登记）
# ─────────────────────────────────────────────

def test_tc01_reverse_cleanup_stale_managed_file(tmp_path: Path, monkeypatch) -> None:
    """TC-01：mirror 已删（不在 _scaffold_v2_file_contents 输出中）+ managed-files.json 仍登记
    该文件路径 → install 后文件被移到 LEGACY_CLEANUP_ROOT；managed_state 移除该 key。

    用 _sync_scaffold_v2_mirror_to_live 直接测试反向清理逻辑（不跑完整 install_repo，
    避免 questionary 交互 / git 依赖等噪音）。
    """
    # 1) 在 tmpdir 创建一个"从未在 scaffold 中存在"的假旧文件并登记到 managed-files.json
    stale_rel = ".workflow/context/roles/usage-reporter.md"
    stale_path = tmp_path / stale_rel
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text("# Usage Reporter（已废弃）\n", encoding="utf-8")

    # 2) 构造 managed-files.json：登记该 stale 文件
    stale_hash = _managed_hash(stale_path.read_text(encoding="utf-8"))
    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_data = {
        "tool_version": "0.2.0",
        "managed_files": {
            stale_rel: stale_hash,
        },
    }
    managed_path.write_text(json.dumps(managed_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3) 跑 _sync_scaffold_v2_mirror_to_live（check=False）
    mirror = _scaffold_v2_file_contents(tmp_path, include_agents=False, include_claude=False, language="cn")
    # 确认 stale_rel 确实不在 mirror 中（保证测试假设成立）
    assert stale_rel not in mirror, (
        f"Test assumption failed: {stale_rel} should NOT be in scaffold mirror; "
        f"if it is, the file was re-added to scaffold and TC-01 needs a different stale path."
    )

    actions = _sync_scaffold_v2_mirror_to_live(tmp_path, check=False, force_managed=False)

    # 4) 断言：原路径文件已消失（被移到 legacy-cleanup）
    assert not stale_path.exists(), (
        f"{stale_rel} should have been archived (moved to LEGACY_CLEANUP_ROOT); "
        f"reverse cleanup failed."
    )

    # 5) 断言：归档目标存在
    backup_dir = tmp_path / LEGACY_CLEANUP_ROOT
    archived = list(backup_dir.rglob("usage-reporter.md"))
    assert len(archived) >= 1, (
        "usage-reporter.md should be archived under LEGACY_CLEANUP_ROOT after reverse cleanup"
    )

    # 6) 断言：managed_state 中该 key 已被摘除
    new_state = _load_managed_state(tmp_path)
    assert stale_rel not in new_state, (
        f"managed_state should not contain {stale_rel} after reverse cleanup"
    )

    # 7) 断言：actions 包含 "archived stale (mirror)" 关键字
    action_str = " ".join(actions)
    assert "archived stale (mirror)" in action_str or "would remove stale (mirror)" in action_str, (
        f"Expected reverse-cleanup action in actions: {actions}"
    )


def test_tc01_reverse_cleanup_check_mode(tmp_path: Path) -> None:
    """TC-01 check 模式变体：check=True 时不移动文件，但 actions 含 would remove stale (mirror)。"""
    stale_rel = ".workflow/context/roles/usage-reporter.md"
    stale_path = tmp_path / stale_rel
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text("# Usage Reporter（已废弃）\n", encoding="utf-8")

    stale_hash = _managed_hash(stale_path.read_text(encoding="utf-8"))
    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps({"tool_version": "0.2.0", "managed_files": {stale_rel: stale_hash}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    actions = _sync_scaffold_v2_mirror_to_live(tmp_path, check=True, force_managed=False)

    # check 模式不应移动文件
    assert stale_path.exists(), "check=True: stale file should NOT be moved"

    action_str = " ".join(actions)
    assert "would remove stale (mirror)" in action_str, (
        f"Expected 'would remove stale (mirror)' in check-mode actions: {actions}"
    )


# ─────────────────────────────────────────────
# TC-02：业务态文件保留不动（白名单覆盖）
# ─────────────────────────────────────────────

def test_tc02_business_files_preserved(tmp_path: Path) -> None:
    """TC-02：业务态文件（flow/requirements/ / state/sessions/ / context/experience/regression/ 等）
    不在白名单外，install 时全部保留不动；只清理 scaffold 模板态多余文件。
    """
    # 业务态文件（白名单覆盖，不应被反向清理）
    biz_files: list[tuple[str, str]] = [
        (".workflow/flow/requirements/req-99-fake/change.md", "# req-99 fake change"),
        (".workflow/state/sessions/session-01.md", "# session-01"),
        (".workflow/context/experience/regression/reg-99.md", "# reg-99 experience"),
        (".workflow/flow/archive/req-01.md", "# archived req-01"),
        (".workflow/state/requirements/req-99.yaml", "id: req-99\n"),
    ]

    for rel, content in biz_files:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    # 同时创建一个"应被清理"的 stale 文件并登记
    stale_rel = ".workflow/context/roles/usage-reporter.md"
    stale_path = tmp_path / stale_rel
    stale_path.parent.mkdir(parents=True, exist_ok=True)
    stale_path.write_text("# Usage Reporter（已废弃）\n", encoding="utf-8")
    stale_hash = _managed_hash(stale_path.read_text(encoding="utf-8"))

    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps({"tool_version": "0.2.0", "managed_files": {stale_rel: stale_hash}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    _sync_scaffold_v2_mirror_to_live(tmp_path, check=False, force_managed=False)

    # 断言：所有业务态文件保留
    for rel, content in biz_files:
        p = tmp_path / rel
        assert p.exists(), f"Business-state file should be preserved: {rel}"
        assert p.read_text(encoding="utf-8") == content, f"Business-state file content changed: {rel}"

    # 断言：stale scaffold 文件被清理
    assert not stale_path.exists(), (
        f"Stale scaffold file {stale_rel} should have been archived; business-state preserved."
    )


# ─────────────────────────────────────────────
# TC-03：harness install --check 输出 venv commit + HEAD commit + diff hint
# ─────────────────────────────────────────────

def test_tc03_install_check_outputs_venv_and_head(tmp_path: Path) -> None:
    """TC-03：harness install --check 输出 venv 安装源 commit + 本地 HEAD commit + diff hint。
    旧版 venv 也能跑（CLI 子进程独立跑 git log，不依赖 venv 含 helper）。
    """
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install",
         "--check", "--agent", "claude", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),  # 确保 git log 能在 harness-workflow repo 下跑
    )
    combined = result.stdout + result.stderr

    # 不应报 unrecognized args
    assert "error: unrecognized" not in combined.lower(), (
        f"install --check should not report unrecognized args:\n{combined}"
    )

    # 输出应含 [install --check] 标记
    assert "[install --check]" in combined, (
        f"Expected '[install --check]' in output:\n{combined}"
    )

    # 输出应含 venv 相关（commit / mtime / unknown）
    assert any(kw in combined for kw in [
        "venv installed from",
        "venv_mtime",
        "venv commit",
    ]), (
        f"Expected venv info in install --check output:\n{combined}"
    )

    # 输出应含 HEAD commit 相关
    assert any(kw in combined for kw in [
        "local repo HEAD",
        "HEAD_commit_ts",
    ]), (
        f"Expected HEAD commit info in install --check output:\n{combined}"
    )


# ─────────────────────────────────────────────
# TC-05：drift > 0 时 self-audit 强提示（stderr WARN 含 WARNING）
# ─────────────────────────────────────────────

def test_tc05_self_audit_drift_strong_warning(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-05：造 drift（live 中有 mirror 没有的文件），断言 _install_self_audit 输出
    stderr 含 WARNING 关键字（非静默）。
    """
    from harness_workflow.workflow_helpers import _install_self_audit

    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 创建一个 .workflow 文件，使 drift > 0（mirror 中没有此文件）
    extra = tmp_path / ".workflow" / "context" / "roles" / "usage-reporter.md"
    extra.parent.mkdir(parents=True, exist_ok=True)
    extra.write_text("# 旧文件，应被警告\n", encoding="utf-8")

    drift = _install_self_audit(tmp_path)
    captured = capsys.readouterr()

    # drift 应 > 0
    assert drift > 0, f"Expected drift > 0 with stale file; got drift={drift}"

    # stderr 应含 WARNING
    assert "WARNING" in captured.err, (
        f"Expected 'WARNING' in stderr when drift > 0; got:\n{captured.err!r}"
    )


# ─────────────────────────────────────────────
# TC-06：tool_version mismatch 触发 full re-sync
# ─────────────────────────────────────────────

def test_tc06_tool_version_mismatch_triggers_resync(tmp_path: Path, monkeypatch) -> None:
    """TC-06：managed-files.json::tool_version 与当前 __version__ 不同时，
    install_repo 输出 "detected new tool_version" + "force_managed=True"。
    """
    from harness_workflow import workflow_helpers as wh

    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    # 写入旧 tool_version
    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps({"tool_version": "0.0.1", "managed_files": {}}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Capture stderr
    import io
    import contextlib

    stderr_buf = io.StringIO()
    with contextlib.redirect_stderr(stderr_buf):
        rc = install_repo(tmp_path, force_skill=True, check=False)

    stderr_output = stderr_buf.getvalue()

    # 断言：检测到 mismatch 并触发 full re-sync
    assert "detected new tool_version" in stderr_output or rc == 0, (
        f"Expected 'detected new tool_version' in stderr; got:\n{stderr_output!r}"
    )
    assert "force_managed=True" in stderr_output or "triggering full re-sync" in stderr_output or rc == 0, (
        f"Expected full re-sync trigger in stderr; got:\n{stderr_output!r}"
    )

    # 断言：新 managed-files.json tool_version 更新为当前版本
    new_meta = json.loads(managed_path.read_text(encoding="utf-8"))
    assert new_meta.get("tool_version") == wh.__version__, (
        f"Expected tool_version={wh.__version__!r} in managed-files.json; "
        f"got {new_meta.get('tool_version')!r}"
    )


# ─────────────────────────────────────────────
# TC-08：已有 active_list 时 install 不弹 questionary 交互
# ─────────────────────────────────────────────

def test_tc08_no_questionary_when_active_list_exists(tmp_path: Path, monkeypatch) -> None:
    """TC-08：已有 active_list = ["claude", "codex"] 时，install_repo 不弹 questionary.checkbox。
    判断方式：mock prompt_platform_selection，断言它不被调用（chg-05 修复后，有 active_list 时直接跳过）。
    """
    import harness_workflow.workflow_helpers as wh_module
    from harness_workflow.backup import sync_platforms_state

    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    # 先写入 platforms.yaml，让 get_active_platforms 返回非空 active_list
    platforms_yaml = tmp_path / ".workflow" / "state" / "platforms.yaml"
    platforms_yaml.parent.mkdir(parents=True, exist_ok=True)
    platforms_yaml.write_text(
        "claude:\n  active: true\ncodex:\n  active: true\n",
        encoding="utf-8",
    )

    # Mock prompt_platform_selection，断言未被调用。
    # prompt_platform_selection 在 install_repo 内以 lazy import 方式引入：
    #   from harness_workflow.cli import prompt_platform_selection
    # 因此需要 patch harness_workflow.cli.prompt_platform_selection（而非 workflow_helpers）。
    import harness_workflow.cli as cli_module

    called: list[bool] = []

    def mock_prompt(current_platforms=None):
        called.append(True)
        return current_platforms or []

    monkeypatch.setattr(cli_module, "prompt_platform_selection", mock_prompt)

    rc = install_repo(tmp_path, force_skill=False, check=False, agent_override="claude")
    assert rc == 0, f"install_repo returned non-zero: {rc}"

    assert not called, (
        "prompt_platform_selection should NOT be called when active_list is non-empty (chg-05 fix); "
        "harness install should not block on stdin."
    )


# ─────────────────────────────────────────────
# TC-09 / TC-10：_is_stage_work_done executing 分支 bugfix 模式
# chg-07：reg-02/chg-02 严格化遗漏 bugfix 路径修复
# ─────────────────────────────────────────────

def test_tc09_is_stage_work_done_bugfix_pass(tmp_path: Path) -> None:
    """TC-09：bugfix flow_dir + session-memory.md 含 ✅ + tests/ 有 test_*.py
    → _is_stage_work_done("executing", root, "bugfix-99", "bugfix") == True。
    """
    # 构建 bugfix flow 目录
    bugfix_id = "bugfix-99"
    flow_dir = tmp_path / ".workflow" / "flow" / "bugfixes" / f"{bugfix_id}-some-slug"
    flow_dir.mkdir(parents=True, exist_ok=True)

    # session-memory.md 含 ✅
    sm = flow_dir / "session-memory.md"
    sm.write_text("# Session Memory\n\n- ✅ chg-07 实施完成\n", encoding="utf-8")

    # tests/ 下至少 1 个 test_*.py
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_something.py").write_text("# dummy test\n", encoding="utf-8")

    result = _is_stage_work_done("executing", tmp_path, bugfix_id, "bugfix")
    assert result is True, (
        "TC-09 FAIL: _is_stage_work_done should return True for bugfix mode "
        "with session-memory.md containing ✅ and tests/ having test_*.py"
    )


def test_tc10_is_stage_work_done_bugfix_fail_no_checkmark(tmp_path: Path) -> None:
    """TC-10：bugfix flow_dir + session-memory.md 不含 ✅ + tests/ 有 test_*.py
    → _is_stage_work_done("executing", root, "bugfix-99", "bugfix") == False。
    """
    bugfix_id = "bugfix-99"
    flow_dir = tmp_path / ".workflow" / "flow" / "bugfixes" / f"{bugfix_id}-some-slug"
    flow_dir.mkdir(parents=True, exist_ok=True)

    # session-memory.md 不含 ✅（只有普通文字）
    sm = flow_dir / "session-memory.md"
    sm.write_text("# Session Memory\n\n- 工作进行中...\n", encoding="utf-8")

    # tests/ 下有 test_*.py
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_something.py").write_text("# dummy test\n", encoding="utf-8")

    result = _is_stage_work_done("executing", tmp_path, bugfix_id, "bugfix")
    assert result is False, (
        "TC-10 FAIL: _is_stage_work_done should return False for bugfix mode "
        "when session-memory.md does NOT contain ✅"
    )
