"""bugfix-9（force-managed 透传修复 + user-write 门禁误报修复）回归测试。

覆盖范围：
- TC-A1：init_repo(force_managed=True) 调用链——用户改过的 managed 文件被正确覆盖，不出现误跳过
- TC-A2：grep 验证 install_repo 内对 init_repo 的调用含 force_managed=force_managed（不硬编码 False）
- TC-B1：user project + skill 工具产出文件 → check_user_write_protected_zones exit 0（不误报）
- TC-B2：user project + .workflow/ 野文件 → check_user_write_protected_zones exit 1（仍能拦截）
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

from harness_workflow.validate_contract import check_user_write_protected_zones  # noqa: E402
from harness_workflow.workflow_helpers import (  # noqa: E402
    MANAGED_STATE_PATH,
    _managed_hash,
    _sync_requirement_workflow_managed_files,
    init_repo,
)


# ─────────────────────────────────────────────────────────────────────────────
# TC-A1：init_repo(force_managed=True) 调用链——用户改过的 managed 文件被覆盖
# ─────────────────────────────────────────────────────────────────────────────

def _make_user_project(tmp_path: Path) -> None:
    """最小 harness 结构（无 pyproject.toml / src/harness_workflow，确保 user project 模式）。"""
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, check=True, capture_output=True,
    )


def test_tc_a1_init_repo_force_managed_true_overwrites_modified(tmp_path: Path, monkeypatch) -> None:
    """TC-A1：init_repo(force_managed=True) 时，用户改过的 managed 文件应被覆盖，
    stderr 不出现 'skipping user-modified'。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _make_user_project(tmp_path)

    from harness_workflow.workflow_helpers import (
        _managed_file_contents,
        ensure_config,
    )

    # 确保 config 存在
    ensure_config(tmp_path)
    config = ensure_config(tmp_path)
    language = config.get("language", "cn")

    # 获取一个 managed 文件内容
    contents = _managed_file_contents(
        tmp_path,
        language=language,
        include_agents=False,
        include_claude=False,
        active_agent=None,
    )
    if not contents:
        pytest.skip("No managed files available for this test")

    # 选第一个非空文件
    target_rel, expected_content = next(iter(contents.items()))
    target_path = tmp_path / target_rel

    # 写入"用户改过"的版本
    modified_content = expected_content + "\n# user-modified for test\n"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(modified_content, encoding="utf-8")

    # 登记 managed-files.json：模拟"工具写入后被用户改"（hash = 原始内容 hash）
    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps(
            {"tool_version": "0.1.0", "managed_files": {target_rel: _managed_hash(expected_content)}},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # 调用 init_repo(force_managed=True)
    stderr_buf = io.StringIO()
    with redirect_stderr(stderr_buf):
        rc = init_repo(tmp_path, write_agents=False, write_claude=False, force_managed=True)

    stderr_out = stderr_buf.getvalue()

    # force_managed=True 时不应出现 "skipping user-modified"
    assert "skipping user-modified" not in stderr_out, (
        f"TC-A1 FAIL: force_managed=True should NOT produce 'skipping user-modified'; "
        f"got stderr:\n{stderr_out!r}"
    )
    # 文件应被覆盖为原始内容
    actual_content = target_path.read_text(encoding="utf-8")
    assert actual_content == expected_content, (
        f"TC-A1 FAIL: file should be overwritten to expected content, "
        f"but got:\n{actual_content[:200]!r}"
    )


def test_tc_a1_init_repo_force_managed_false_skips_modified(tmp_path: Path, monkeypatch) -> None:
    """TC-A1 对照组：init_repo(force_managed=False) 时，用户改过的 managed 文件应被跳过。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _make_user_project(tmp_path)

    from harness_workflow.workflow_helpers import (
        _managed_file_contents,
        ensure_config,
    )

    ensure_config(tmp_path)
    config = ensure_config(tmp_path)
    language = config.get("language", "cn")

    contents = _managed_file_contents(
        tmp_path,
        language=language,
        include_agents=False,
        include_claude=False,
        active_agent=None,
    )
    if not contents:
        pytest.skip("No managed files available for this test")

    target_rel, expected_content = next(iter(contents.items()))
    target_path = tmp_path / target_rel

    modified_content = expected_content + "\n# user-modified for test\n"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(modified_content, encoding="utf-8")

    managed_path = tmp_path / MANAGED_STATE_PATH
    managed_path.parent.mkdir(parents=True, exist_ok=True)
    managed_path.write_text(
        json.dumps(
            {"tool_version": "0.1.0", "managed_files": {target_rel: _managed_hash(expected_content)}},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # force_managed=False：用户修改应被保护
    rc = init_repo(tmp_path, write_agents=False, write_claude=False, force_managed=False)

    # 文件内容应保持用户修改版本
    actual_content = target_path.read_text(encoding="utf-8")
    assert actual_content == modified_content, (
        f"TC-A1 对照：force_managed=False 应保留用户修改，但文件内容变了:\n{actual_content[:200]!r}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TC-A2：grep 验证 install_repo 内调用 init_repo 含 force_managed=force_managed
# ─────────────────────────────────────────────────────────────────────────────

def test_tc_a2_install_repo_calls_init_repo_with_force_managed() -> None:
    """TC-A2：workflow_helpers.py 中 install_repo 对 init_repo 的调用必须含 force_managed=force_managed。

    直接 grep 源码，断言 install_repo 内有且仅有正确的透传调用形式。
    确保不再出现裸 init_repo(...) 不传 force_managed 的硬编码形态（bugfix-9 修复点）。
    """
    helpers_path = REPO_ROOT / "src" / "harness_workflow" / "workflow_helpers.py"
    source = helpers_path.read_text(encoding="utf-8")

    # 提取 install_repo 函数体（从 def install_repo 到下一个 def 级函数）
    lines = source.splitlines()
    in_install_repo = False
    install_repo_lines: list[str] = []
    for line in lines:
        if line.startswith("def install_repo("):
            in_install_repo = True
        elif in_install_repo and line.startswith("def ") and "install_repo" not in line:
            break
        if in_install_repo:
            install_repo_lines.append(line)

    install_repo_body = "\n".join(install_repo_lines)

    # install_repo 内部对 init_repo 的调用必须带 force_managed=force_managed
    assert "init_repo(" in install_repo_body, (
        "TC-A2 FAIL: install_repo should call init_repo()"
    )
    assert "force_managed=force_managed" in install_repo_body, (
        "TC-A2 FAIL: install_repo's call to init_repo must pass force_managed=force_managed; "
        "hardcoded False is the bugfix-9 regression point"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TC-B1：user project + skill 工具产出文件 → check_user_write_protected_zones exit 0
# ─────────────────────────────────────────────────────────────────────────────

def test_tc_b1_skill_tool_output_not_reported_as_violation(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-B1：tmpdir user project（无 src/、无 pyproject.toml::name=harness-workflow）+
    含 `.claude/skills/harness/SKILL.md`（工具产出）→
    check_user_write_protected_zones exit 0（不报 violation）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 模拟 install_local_skills 产出的 skill 文件
    skill_file = tmp_path / ".claude" / "skills" / "harness" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# Harness Skill\n", encoding="utf-8")

    # 再加几个 commands 文件（模拟 install_local_skills 完整产出）
    cmd_file = tmp_path / ".codex" / "commands" / "harness.md"
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    cmd_file.write_text("# Harness Command\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0, (
        f"TC-B1 FAIL: skill/commands tool output should NOT trigger violation; "
        f"got rc={rc}\nstderr:\n{captured.err!r}"
    )
    assert "violation" not in captured.err, (
        f"TC-B1 FAIL: no violation expected for skill/commands tool output; "
        f"got:\n{captured.err!r}"
    )


def test_tc_b1_skill_tool_output_subprocess(tmp_path: Path, monkeypatch) -> None:
    """TC-B1 subprocess 变体：CLI harness validate --contract user-write-protected-zones 在含
    skill 工具产出的 user project 中 exit 0。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    skill_file = tmp_path / ".claude" / "skills" / "harness" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# Harness Skill\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "user-write-protected-zones", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "HARNESS_DEV_REPO_ROOT": ""},
    )

    assert result.returncode == 0, (
        f"TC-B1 subprocess FAIL: skill tool output should exit 0; "
        f"got {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TC-B2：user project + .workflow/ 野文件 → check_user_write_protected_zones ABORT exit 1
# ─────────────────────────────────────────────────────────────────────────────

def test_tc_b2_workflow_wild_file_still_blocked(tmp_path: Path, monkeypatch, capsys) -> None:
    """TC-B2：tmpdir user project + 在 `.workflow/context/roles/my-custom.md` 写野文件 →
    check_user_write_protected_zones ABORT exit 1（chg-02 移除 skill/commands 后仍能拦真野文件）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 真野文件：用户手写的 .workflow/ 角色文件
    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# My Custom Role\n", encoding="utf-8")

    # 同时存在 skill 工具产出（不应干扰）
    skill_file = tmp_path / ".claude" / "skills" / "harness" / "SKILL.md"
    skill_file.parent.mkdir(parents=True, exist_ok=True)
    skill_file.write_text("# Harness Skill\n", encoding="utf-8")

    rc = check_user_write_protected_zones(tmp_path)
    captured = capsys.readouterr()

    assert rc >= 1, (
        f"TC-B2 FAIL: .workflow/ wild file should trigger ABORT; got rc={rc}\nstderr:\n{captured.err!r}"
    )
    assert "violation" in captured.err, (
        f"TC-B2 FAIL: expected 'violation' in stderr; got:\n{captured.err!r}"
    )
    assert ".workflow/context/roles/my-custom.md" in captured.err, (
        f"TC-B2 FAIL: expected wild file path in stderr; got:\n{captured.err!r}"
    )


def test_tc_b2_workflow_wild_file_subprocess(tmp_path: Path, monkeypatch) -> None:
    """TC-B2 subprocess 变体：含 .workflow/ 野文件的 user project exit 1。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    wild_file = tmp_path / ".workflow" / "context" / "roles" / "my-custom.md"
    wild_file.parent.mkdir(parents=True, exist_ok=True)
    wild_file.write_text("# My Custom Role\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "user-write-protected-zones", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "HARNESS_DEV_REPO_ROOT": ""},
    )

    assert result.returncode == 1, (
        f"TC-B2 subprocess FAIL: .workflow/ wild file should exit 1; "
        f"got {result.returncode}\nstdout:{result.stdout}\nstderr:{result.stderr}"
    )
    assert "violation" in result.stderr, (
        f"TC-B2 subprocess FAIL: expected 'violation' in stderr; got:\n{result.stderr!r}"
    )
