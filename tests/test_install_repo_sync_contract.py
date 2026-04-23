"""req-36（harness install 同步契約完整性修復）/ chg-02：install_repo sync 契約測試

AC-4 + AC-7 coverage:
  test 1: tmp_path 全新 install 後，live 與 scaffold_v2 mirror 排除白名單後零差異
  test 2: mock drift → _install_self_audit() 向 stderr 報警
"""
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    SCAFFOLD_V2_ROOT,
    _install_self_audit,
    _scaffold_v2_file_contents,
    install_repo,
)

# 白名單（承 requirement.md §2.3 C 段 12 條 + A27 missing-log.yaml 特殊處理）
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
    "tools/index/missing-log.yaml",  # A27 運行時累積，mirror 是模板態空值
)


@pytest.mark.xfail(
    strict=False,
    reason="req-36/chg-02: depends on chg-03 reconcile completing; remove xfail after chg-03 merged",
)
def test_install_repo_diffs_against_scaffold_v2_mirror_zero(tmp_path, monkeypatch):
    """req-36（harness install 同步契約完整性修復）/ chg-02 AC-7 測試 1：
    tmp_path 全新 install 後，live 與 scaffold_v2 mirror 排除白名單後零差異。
    依賴 chg-03（歷史漂移 reconcile（live → scaffold_v2 mirror 27+ 文件 + B 類 mirror → live 2 文件））reconcile 已完成；
    chg-03 前可能因歷史漂移 fail（已標 xfail(strict=False)）。
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
