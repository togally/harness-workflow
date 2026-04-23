"""req-36（harness install 同步契约完整性修复）/ chg-02 + chg-05 + chg-06：install_repo sync 契约测试

AC-4 + AC-7 coverage:
  chg-02 test 1: tmp_path 全新 install 后，live 与 scaffold_v2 mirror 排除白名单后零差异
  chg-02 test 2: mock drift → _install_self_audit() 向 stderr 报警
  chg-05 test 3-6: install_repo 末尾追加 mirror→live 全量同步契约
  chg-06 test 7-8: _install_self_audit 触发面解锁（删 pyproject 锚点 + env 保留）
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    MANAGED_STATE_PATH,
    SCAFFOLD_V2_ROOT,
    _SCAFFOLD_V2_MIRROR_WHITELIST,
    _install_self_audit,
    _load_managed_state,
    _managed_hash,
    _save_managed_state,
    _scaffold_v2_file_contents,
    _sync_scaffold_v2_mirror_to_live,
    install_repo,
)

# 白名单（承 requirement.md §2.3 C 段 12 条 + A27 missing-log.yaml + chg-05/06 template-rebuild 4 条）
# 与 src/harness_workflow/workflow_helpers.py::_SCAFFOLD_V2_MIRROR_WHITELIST 保持一致。
_WHITELIST = (
    "state/sessions",
    "state/requirements",
    "state/bugfixes",
    "state/feedback",
    "state/runtime.yaml",
    "state/action-log.md",
    "flow/archive",
    "flow/requirements",
    "flow/suggestions",
    "context/backup",
    "context/experience/stage",
    "workflow/archive",
    "tools/index/missing-log.yaml",  # A27 运行时累积，mirror 是模板态空值
    # chg-05 / chg-06 扩展：post-install 系统重建 / 项目专属渲染（mirror 比对会一直 drift，需豁免）
    "context/experience/index.md",
    "context/project-profile.md",
    "CLAUDE.md",
    "AGENTS.md",
)


def test_install_repo_diffs_against_scaffold_v2_mirror_zero(tmp_path, monkeypatch):
    """req-36（harness install 同步契约完整性修复）/ chg-02 AC-7 测试 1：
    tmp_path 全新 install 后，live 与 scaffold_v2 mirror 排除白名单后零差异。
    依赖 chg-03（历史漂移 reconcile（live → scaffold_v2 mirror 27+ 文件 + B 类 mirror → live 2 文件）） reconcile 已完成；
    chg-05（install_repo 末尾追加 mirror→live 全量同步）落地后 tmp_path install 应 zero-drift（解 xfail）。
    """
    # 防止誤觸發本倉庫 self-audit 噪聲（tmp_path 不是本倉庫，本來就不觸發；顯式 unset）
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)

    # 最小 git 環境（install_repo 內部調用 git status 等命令）
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0

    mirror = _scaffold_v2_file_contents(
        tmp_path, include_agents=False, include_claude=False, language="cn"
    )
    drifts = []
    for relative, expected in mirror.items():
        if any(w in relative for w in _WHITELIST):
            continue
        live = tmp_path / relative
        if not live.exists():
            drifts.append(f"missing: {relative}")
            continue
        if live.read_text(encoding="utf-8") != expected:
            drifts.append(f"differs: {relative}")
    assert drifts == [], (
        f"req-36/chg-02: unexpected drift(s) after install_repo(tmp_path): {drifts[:5]}"
    )


def test_install_self_audit_reports_drift_to_stderr(tmp_path, monkeypatch, capsys):
    """req-36（harness install 同步契約完整性修復）/ chg-02 AC-4 測試 2：
    mock _scaffold_v2_file_contents 返回多一條虛構 drift，
    _install_self_audit 應 stderr 報警。
    """
    # 強制 self-audit 觸發面（偽裝 tmp_path 是本倉庫）
    monkeypatch.setenv("HARNESS_DEV_REPO_ROOT", str(tmp_path))

    fake_mirror = {".workflow/context/__test_drift__.md": "drift-content-xyz"}
    monkeypatch.setattr(
        "harness_workflow.workflow_helpers._scaffold_v2_file_contents",
        lambda *a, **kw: fake_mirror,
    )
    drift_count = _install_self_audit(tmp_path)
    captured = capsys.readouterr()
    assert drift_count >= 1, "expected ≥1 drift when mirror has file missing in live"
    assert "[install_repo:self-audit] drift detected" in captured.err, (
        f"expected drift alert in stderr; got: {captured.err!r}"
    )
    assert "WARNING" in captured.err, (
        f"expected WARNING summary in stderr; got: {captured.err!r}"
    )


# --- chg-05（install_repo 末尾追加 mirror→live 全量同步） + chg-06（解锁 _install_self_audit）共享 fixture ---


def _git_init(root: Path) -> None:
    """最小 git 初始化（install_repo 内部调用 git status 等命令）。"""
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


@pytest.fixture
def installed_tmp_repo(tmp_path, monkeypatch, capsys):
    """req-36 / chg-05 fixture：tmp_path 上初始化 git + 跑一次 install_repo，返回干净已装态。"""
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)
    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0, "install_repo baseline failed"
    # 清掉 fixture 阶段的 stdout/stderr，避免后续断言混入
    capsys.readouterr()
    return tmp_path


# --- chg-05 STEP-1：4 个新用例 ---


def test_install_repo_full_mirror_sync_creates_missing_files(installed_tmp_repo, capsys):
    """req-36 / chg-05 AC-7 测试 3：
    install_repo 末尾应跑全量 mirror→live 同步 helper：
    1. 删除 mirror 内已存在的两个文件后，第二次 install 应被铺回（managed sync 与 mirror sync 协作）。
    2. 直接以 mirror sync helper 处理 missing-only 场景：构造 helper 单独触发的 missing 文件，
       验证 helper 走分支 2（live 不存在 → created (mirror) action）。

    设计注：因 scaffold_v2 ⊆ _managed_file_contents，managed sync 在前已处理大部分 missing；
    本 helper 是 defense-in-depth，对仍 drift 的 mirror 文件走 (mirror) 写入路径。
    """
    root = installed_tmp_repo
    target_a = root / ".workflow" / "context" / "roles" / "project-reporter.md"
    target_b = root / ".workflow" / "context" / "role-model-map.yaml"
    assert target_a.exists(), "fixture sanity: project-reporter.md should exist after baseline install"
    assert target_b.exists(), "fixture sanity: role-model-map.yaml should exist after baseline install"
    target_a.unlink()
    target_b.unlink()
    assert not target_a.exists() and not target_b.exists()

    rc = install_repo(root, force_skill=True, check=False)
    captured_install = capsys.readouterr()
    assert rc == 0
    assert target_a.exists(), (
        "managed sync should re-create deleted mirror file project-reporter.md"
    )
    assert target_b.exists(), (
        "managed sync should re-create deleted mirror file role-model-map.yaml"
    )
    expected_a = (
        SCAFFOLD_V2_ROOT / ".workflow" / "context" / "roles" / "project-reporter.md"
    ).read_text(encoding="utf-8")
    expected_b = (
        SCAFFOLD_V2_ROOT / ".workflow" / "context" / "role-model-map.yaml"
    ).read_text(encoding="utf-8")
    assert target_a.read_text(encoding="utf-8") == expected_a
    assert target_b.read_text(encoding="utf-8") == expected_b

    # 直接调 mirror sync helper：删除非白名单 mirror 文件 + 不刷 managed_state，
    # 验证 helper 自身走分支 2 / 6（创建 + 用户改过覆盖路径）。
    target_a.unlink()  # 再次删除，模拟 managed sync 之后仍有 drift
    actions = _sync_scaffold_v2_mirror_to_live(root, check=False, force_managed=False)
    assert any("created (mirror)" in a and "project-reporter.md" in a for a in actions), (
        f"expected 'created (mirror) ... project-reporter.md' in helper actions; got: {actions}"
    )
    assert target_a.exists() and target_a.read_text(encoding="utf-8") == expected_a, (
        "helper 直接调用应铺回 mirror 模板态"
    )
    # 至少应有 'synced mirror→live' 汇总行（drift_count > 0 时追加）
    assert any("synced mirror→live" in a for a in actions), (
        f"expected 'synced mirror→live' summary in helper actions; got: {actions}"
    )


def test_install_repo_full_mirror_sync_respects_user_modified(installed_tmp_repo, capsys):
    """req-36 / chg-05 AC-7 测试 4：
    base-role.md 改动且 managed-files.json 登记其原 hash 后，第二次 install 默认（force_managed=False）
    应保留用户改动 + stderr 含 skipped user-modified + --force-managed 提示。
    """
    root = installed_tmp_repo
    target = root / ".workflow" / "context" / "roles" / "base-role.md"
    assert target.exists(), "fixture sanity: base-role.md should exist after baseline install"
    original = target.read_text(encoding="utf-8")
    user_edit = original + "\n\n## 用户附加段（chg-05 test）\n"
    target.write_text(user_edit, encoding="utf-8")

    # 在 managed-files.json 登记其"原 hash"，模拟 harness 落盘后用户改过
    relative = ".workflow/context/roles/base-role.md"
    state = _load_managed_state(root)
    state[relative] = _managed_hash(original)
    _save_managed_state(root, state)

    rc = install_repo(root, force_skill=True, check=False, force_managed=False)
    captured = capsys.readouterr()
    assert rc == 0
    actual = target.read_text(encoding="utf-8")
    assert actual == user_edit, (
        "chg-05 sync helper must NOT overwrite user-modified file when force_managed=False"
    )
    # 既有 managed sync 与 chg-05 mirror sync helper 任一发出 user-modified 提示均可接受
    # （文案：'skipping user-modified file' or 'skipped user-modified'，均含 user-modified）
    assert "user-modified" in captured.err and relative in captured.err, (
        f"expected stderr containing 'user-modified ... base-role.md'; got: {captured.err[-2000:]!r}"
    )
    assert "--force-managed" in captured.err, (
        f"expected '--force-managed' hint in stderr; got: {captured.err[-2000:]!r}"
    )
    # chg-05 helper 自证：mirror sync helper 应在 stderr 也用 [install_repo:mirror-sync] 前缀报告
    assert "[install_repo:mirror-sync]" in captured.err, (
        f"expected '[install_repo:mirror-sync]' prefix in stderr (proves chg-05 helper ran); "
        f"got: {captured.err[-2000:]!r}"
    )


def test_install_repo_full_mirror_sync_force_managed_overwrites(installed_tmp_repo, capsys):
    """req-36 / chg-05 AC-7 测试 5：
    base-role.md 用户改过 + managed-files.json 登记原 hash，force_managed=True 时应被覆盖回 mirror。
    """
    root = installed_tmp_repo
    target = root / ".workflow" / "context" / "roles" / "base-role.md"
    original = target.read_text(encoding="utf-8")
    user_edit = original + "\n\n## 用户附加段（force-managed test）\n"
    target.write_text(user_edit, encoding="utf-8")

    relative = ".workflow/context/roles/base-role.md"
    state = _load_managed_state(root)
    state[relative] = _managed_hash(original)
    _save_managed_state(root, state)

    rc = install_repo(root, force_skill=True, check=False, force_managed=True)
    capsys.readouterr()
    assert rc == 0
    actual = target.read_text(encoding="utf-8")
    # 模板态 = mirror 内容 = original（用户编辑前）
    expected_mirror_path = (
        SCAFFOLD_V2_ROOT / ".workflow" / "context" / "roles" / "base-role.md"
    )
    expected = expected_mirror_path.read_text(encoding="utf-8")
    assert actual == expected, (
        "chg-05 sync helper must overwrite user-modified file when force_managed=True"
    )


def test_install_repo_full_mirror_sync_whitelist_skips_runtime(installed_tmp_repo, capsys):
    """req-36 / chg-05 AC-7 测试 6：
    白名单覆盖项（state/sessions/* + tools/index/missing-log.yaml）即使被用户写入也不应被 sync 触碰。
    """
    root = installed_tmp_repo
    runtime_session = root / ".workflow" / "state" / "sessions" / "foo.md"
    runtime_session.parent.mkdir(parents=True, exist_ok=True)
    runtime_session.write_text("# user session note\n", encoding="utf-8")

    missing_log = root / ".workflow" / "tools" / "index" / "missing-log.yaml"
    missing_log.parent.mkdir(parents=True, exist_ok=True)
    missing_log.write_text("queries:\n  - q1\n  - q2\n", encoding="utf-8")

    rc = install_repo(root, force_skill=True, check=False)
    capsys.readouterr()
    assert rc == 0
    assert runtime_session.exists()
    assert runtime_session.read_text(encoding="utf-8") == "# user session note\n", (
        "chg-05 whitelist must skip state/sessions/* (runtime data, not mirror-synced)"
    )
    assert missing_log.exists()
    assert missing_log.read_text(encoding="utf-8") == "queries:\n  - q1\n  - q2\n", (
        "chg-05 whitelist must skip tools/index/missing-log.yaml (runtime accumulated)"
    )


# --- chg-06 STEP-1：2 个新用例 ---


def test_install_self_audit_runs_in_non_harness_project(tmp_path, monkeypatch, capsys):
    """req-36 / chg-06 AC-4 + AC-7 测试 7：
    pyproject.toml name != "harness-workflow"（或缺失），HARNESS_DEV_REPO_ROOT 也未设时，
    _install_self_audit 仍应跑 mirror 比对，而非早 return 0。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    # 写入非 harness-workflow 的 pyproject，模拟存量项目
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "some-other-project"\n', encoding="utf-8"
    )
    # tmp_path 没有 .workflow/ 实体，mirror 全量 → drift 应远 > 0
    drift_count = _install_self_audit(tmp_path)
    captured = capsys.readouterr()
    assert drift_count > 0, (
        f"expected drift_count > 0 in non-harness project (mirror should compare), got {drift_count}"
    )
    assert "[install_repo:self-audit] drift detected" in captured.err, (
        f"expected drift alert in stderr; got tail: {captured.err[-500:]!r}"
    )


def test_install_self_audit_dev_repo_root_env_skips(tmp_path, monkeypatch, capsys):
    """req-36 / chg-06 AC-7 测试 8：
    HARNESS_DEV_REPO_ROOT env 设为 != tmp_path 时仍应早 return 0（开发期 escape hatch 保留）。
    回归保护：确保 chg-06 删 pyproject 段时不误删 env 段。
    """
    monkeypatch.setenv("HARNESS_DEV_REPO_ROOT", "/tmp/a-different-path-not-tmp_path")
    drift_count = _install_self_audit(tmp_path)
    captured = capsys.readouterr()
    assert drift_count == 0, (
        f"expected drift_count == 0 when HARNESS_DEV_REPO_ROOT != root; got {drift_count}"
    )
    assert captured.err == "", (
        f"expected empty stderr when env-skip path triggers; got: {captured.err!r}"
    )
