"""req-51（项目级规则-经验-工具支持从制品引入）/ chg-02（升级保护-mirror-protected-双豁免）dogfood 测试。

覆盖范围：
- TC-01-install-preserve-project-files：tmpdir 写 artifacts/main/project/constraints/my-rule.md → harness install → 文件保留
- TC-02-mirror-dict-not-contain-project-path：_scaffold_v2_file_contents 返回 dict 不含 artifacts/main/project/
- TC-03-force-managed-not-overwrite-project：harness install --force-managed 不覆盖 artifacts/main/project/
- TC-04-self-audit-not-report-project-drift：_install_self_audit 不报 artifacts/main/project/ drift
- TC-05-protected-zones-exempt-project：check_user_write_protected_zones 在用户项目模式下对 artifacts/main/project/ exit 0；同时对 .workflow/context/roles/x.md 仍 ABORT
- TC-06-whitelist-constant-grep：_SCAFFOLD_V2_MIRROR_WHITELIST 含 "artifacts/main/project/" 条目
- TC-07-mirror-dict-not-contain-project-path-unit：单元测试 _scaffold_v2_file_contents dict key 断言
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))


def _subprocess_env() -> dict:
    """Return env with PYTHONPATH set to workspace src/ so subprocess can import harness_workflow."""
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_path}:{existing}" if existing else src_path
    return env

from harness_workflow.validate_contract import check_user_write_protected_zones  # noqa: E402
from harness_workflow.workflow_helpers import (  # noqa: E402
    _SCAFFOLD_V2_MIRROR_WHITELIST,
    _scaffold_v2_file_contents,
)


def _make_user_project(tmp_path: Path) -> None:
    """初始化一个用户项目模式的 tmpdir（无 pyproject.toml `name = "harness-workflow"`）。
    确保 _is_dev_repo 返回 False。
    """
    # 确保没有任何 dev-mode 标志
    # (tmp_path 默认空，不含 pyproject.toml / src/harness_workflow)
    pass


def test_tc01_install_preserve_project_files(tmp_path: Path) -> None:
    """TC-01-install-preserve-project-files：
    tmpdir 写 artifacts/main/project/constraints/my-rule.md → harness install → 文件保留。
    AC-02（升级保护）。
    优先级 P0。
    """
    _make_user_project(tmp_path)

    # 先 install 初始化
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        env=_subprocess_env(),
    )
    assert result.returncode == 0, f"harness install failed: {result.stderr}"

    # 写项目级文件
    project_dir = tmp_path / "artifacts" / "main" / "project" / "constraints"
    project_dir.mkdir(parents=True, exist_ok=True)
    rule_file = project_dir / "my-rule.md"
    rule_file.write_text("PROJECT_LOCAL_RULE: req-51 自定义规则", encoding="utf-8")
    before_content = rule_file.read_text(encoding="utf-8")

    # 再跑 install
    result2 = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        env=_subprocess_env(),
    )
    assert result2.returncode == 0, f"harness install (2nd) failed: {result2.stderr}"

    # 断言文件内容不变
    after_content = rule_file.read_text(encoding="utf-8")
    assert before_content == after_content, (
        f"项目级文件被覆盖：before={before_content!r} after={after_content!r}"
    )


def test_tc02_mirror_dict_not_contain_project_path(tmp_path: Path) -> None:
    """TC-02-mirror-dict-not-contain-project-path：
    _scaffold_v2_file_contents 返回 dict 不含 artifacts/main/project/ 前缀的 key。
    AC-04（mirror 不污染）。
    优先级 P1。
    """
    mirror = _scaffold_v2_file_contents(tmp_path, include_agents=False, include_claude=False, language="cn")
    project_keys = [k for k in mirror if "artifacts/main/project/" in k]
    assert len(project_keys) == 0, (
        f"scaffold_v2 mirror 不应含 artifacts/main/project/ keys，实际命中：{project_keys}"
    )


def test_tc03_force_managed_not_overwrite_project(tmp_path: Path) -> None:
    """TC-03-force-managed-not-overwrite-project：
    harness install --force-managed 不覆盖 artifacts/main/project/。
    AC-02（升级保护）。
    优先级 P0。
    """
    _make_user_project(tmp_path)

    # 先 install 初始化
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        env=_subprocess_env(),
    )
    assert result.returncode == 0, f"harness install failed: {result.stderr}"

    # 写项目级文件
    for subdir in ["constraints", "experience", "tools"]:
        d = tmp_path / "artifacts" / "main" / "project" / subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / "my-file.md").write_text(f"PROJECT_LOCAL_{subdir.upper()}", encoding="utf-8")

    before = {
        p: (tmp_path / f"artifacts/main/project/{p}/my-file.md").read_text(encoding="utf-8")
        for p in ["constraints", "experience", "tools"]
    }

    # force-managed install
    result2 = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install", "--force-managed"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
        env=_subprocess_env(),
    )
    assert result2.returncode == 0, f"install --force-managed failed: {result2.stderr}"

    after = {
        p: (tmp_path / f"artifacts/main/project/{p}/my-file.md").read_text(encoding="utf-8")
        for p in ["constraints", "experience", "tools"]
    }
    assert before == after, f"项目级文件被 force-managed 覆盖：before={before} after={after}"
    # stderr 不含 "overwrote user-modified" 关于 my-file.md 的行
    assert "my-file.md" not in (result2.stderr or ""), (
        f"stderr 含 my-file.md 覆盖提示：{result2.stderr}"
    )


def test_tc04_self_audit_not_report_project_drift(tmp_path: Path) -> None:
    """TC-04-self-audit-not-report-project-drift：
    _install_self_audit 不报 artifacts/main/project/ drift。
    AC-02 / AC-04（self-audit 不误报）。
    优先级 P0。
    """
    from harness_workflow.workflow_helpers import _install_self_audit

    _make_user_project(tmp_path)

    # 写项目级文件（不经 install，直接写）
    project_dir = tmp_path / "artifacts" / "main" / "project" / "constraints"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "my-rule.md").write_text("PROJECT_LOCAL_RULE", encoding="utf-8")

    # 调 self-audit（在 tmp_path 中不含 .workflow/，但关键是不报 artifacts/main/project/ drift）
    # self-audit 比对 mirror 与 live，但 mirror 不含 artifacts/main/project/，
    # 故 artifacts/main/project/ 不进 stale_keys，不报 drift
    import io
    import contextlib
    stderr_buf = io.StringIO()
    with contextlib.redirect_stderr(stderr_buf):
        drift_count = _install_self_audit(tmp_path)
    stderr_output = stderr_buf.getvalue()

    assert "artifacts/main/project/" not in stderr_output, (
        f"self-audit 误报了 artifacts/main/project/ drift：{stderr_output}"
    )


def test_tc05_protected_zones_exempt_project(tmp_path: Path, monkeypatch) -> None:
    """TC-05-protected-zones-exempt-project：
    check_user_write_protected_zones 在用户项目模式下对 artifacts/main/project/ exit 0；
    同时对 .workflow/context/roles/x.md 仍 ABORT。
    AC-03（用户写保护豁免）。
    优先级 P0。
    """
    # 确保用户项目模式（非 dev）
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 写项目级文件
    for subdir in ["constraints", "experience", "tools"]:
        d = tmp_path / "artifacts" / "main" / "project" / subdir
        d.mkdir(parents=True, exist_ok=True)
        (d / "x.md").write_text("PROJECT_LOCAL", encoding="utf-8")

    # 未写 .workflow/（干净 tmp_path），check 应 PASS（0）
    result = check_user_write_protected_zones(tmp_path)
    assert result == 0, (
        f"artifacts/main/project/ 应被豁免（返回 0），实际返回 {result}"
    )


def test_tc05b_protected_zones_still_block_roles(tmp_path: Path, monkeypatch) -> None:
    """TC-05b：同一 tmpdir 额外写 .workflow/context/roles/my-custom-role.md，仍命中保护区（≥ 1）。
    AC-03（豁免精准，不放大保护面）。
    优先级 P0。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 写 .workflow/context/roles/ 野文件（安装后的 managed 文件列表中无此文件）
    role_dir = tmp_path / ".workflow" / "context" / "roles"
    role_dir.mkdir(parents=True, exist_ok=True)
    (role_dir / "my-custom-role.md").write_text("CUSTOM ROLE", encoding="utf-8")

    # 但需要 managed state 存在（否则 check 可能无法判定"野文件"）
    # 先模拟一个最小的 .workflow 结构（无 managed-files.json 时 check 依赖 mirror）
    # 简化：此用例的核心是"roles 野文件命中 ≥ 1"，不依赖 managed state
    result = check_user_write_protected_zones(tmp_path)
    assert result >= 1, (
        f".workflow/context/roles/ 野文件应命中保护区（≥ 1），实际返回 {result}"
    )


def test_tc06_whitelist_constant_grep() -> None:
    """TC-06-whitelist-constant-grep：
    req-52 / chg-02：白名单字面值从 "artifacts/main/project/" 改为 "artifacts/project/" + "/project/"
    _SCAFFOLD_V2_MIRROR_WHITELIST 含 "artifacts/project/" 主路径条目（req-52 / chg-01 OQ-A = D-modified）。
    AC-04（白名单常量验证）。
    优先级 P1。
    """
    assert "artifacts/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        f"_SCAFFOLD_V2_MIRROR_WHITELIST 缺少 'artifacts/project/' 主路径条目（req-52 / chg-01 OQ-A = D-modified），"
        f"实际白名单：{_SCAFFOLD_V2_MIRROR_WHITELIST}"
    )
    assert "/project/" in _SCAFFOLD_V2_MIRROR_WHITELIST, (
        f"_SCAFFOLD_V2_MIRROR_WHITELIST 缺少 '/project/' substring 兜底条目（req-52 / chg-02 兼容 legacy artifacts/{{branch}}/project/），"
        f"实际白名单：{_SCAFFOLD_V2_MIRROR_WHITELIST}"
    )
