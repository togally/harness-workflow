"""bugfix-4（harness install 升级清理：旧 layout 残留 / .bak / branch 名 / schema 不一致）：
chg-1（install_repo cleanup 扩 layout 残留）+ chg-2（state .bak 残留清理）+ chg-3（schema 探测扩 folder 形态）pytest 覆盖。

Fixture 1 (test_artifacts_layout_removed_by_install_repo):
  模拟存量项目含 `.workflow/flow/artifacts-layout.md` 旧文件
  → install_repo 后该文件被归档（不再存在于原路径）

Fixture 2 (test_bak_files_cleaned_by_install_repo):
  模拟 `.yaml.bak` 残留（同名 .yaml 存在）
  → install_repo 后 .bak 文件被删除（清零）

Fixture 3 (test_schema_folder_audit_warning_not_deleted):
  模拟 `req-XX/` folder 旧 schema（无对应 .yaml）
  → install_repo 后 folder 仍存在（不删）；cleanup_state_bak_files / _migrate_state_files
     输出含 '⚠️' audit 警告
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from harness_workflow.workflow_helpers import (  # noqa: E402
    cleanup_state_bak_files,
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
# Fixture 1：旧 artifacts-layout.md 被 install_repo 归档
# ─────────────────────────────────────────────

def test_artifacts_layout_removed_by_install_repo(tmp_path, monkeypatch):
    """bugfix-4（harness install 升级清理）/ chg-1（install_repo cleanup 扩 layout 残留）：
    存量项目含 `.workflow/flow/artifacts-layout.md` 旧文件（req-39 旧契约），
    运行 install_repo 后该文件被归档，不再位于原路径。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    # 创建旧文件
    flow_dir = tmp_path / ".workflow" / "flow"
    flow_dir.mkdir(parents=True, exist_ok=True)
    old_layout = flow_dir / "artifacts-layout.md"
    old_layout.write_text(
        "# artifacts-layout（旧契约，req-39 时代）\n",
        encoding="utf-8",
    )
    assert old_layout.exists(), "sanity: old artifacts-layout.md should exist before install"

    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0, f"install_repo returned non-zero: {rc}"

    # 断言旧文件已从原路径消失（被归档到 legacy-cleanup/）
    assert not old_layout.exists(), (
        ".workflow/flow/artifacts-layout.md should be archived (not exist at original path) "
        "after install_repo; check LEGACY_CLEANUP_TARGETS includes this path."
    )

    # 断言归档目标确实存在（归档语义，而非删除）
    backup_dir = tmp_path / ".workflow" / "context" / "backup" / "legacy-cleanup"
    archived = list(backup_dir.rglob("artifacts-layout.md"))
    assert len(archived) >= 1, (
        "artifacts-layout.md should be archived under "
        ".workflow/context/backup/legacy-cleanup/ after install_repo"
    )


# ─────────────────────────────────────────────
# Fixture 2：.yaml.bak 残留在 install_repo 后被清零
# ─────────────────────────────────────────────

def test_bak_files_cleaned_by_install_repo(tmp_path, monkeypatch):
    """bugfix-4（harness install 升级清理）/ chg-2（state .bak 残留清理 helper）：
    存量项目含 `.workflow/state/requirements/req-03.yaml.bak`（同名 .yaml 存在），
    运行 install_repo 后 .bak 文件被删除（unlink）。
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    req_state_dir = tmp_path / ".workflow" / "state" / "requirements"
    req_state_dir.mkdir(parents=True, exist_ok=True)

    # 创建一个合法的 .yaml（已迁移好）
    req_yaml = req_state_dir / "req-03.yaml"
    req_yaml.write_text(
        "id: req-03\ntitle: 测试需求\nstatus: done\ncreated_at: '2024-01-01'\n"
        "started_at: '2024-01-01'\ncompleted_at: null\narchived_at: null\nstage_timestamps: {}\n",
        encoding="utf-8",
    )

    # 模拟 _migrate_state_files 遗留的 .bak
    bak_file = req_state_dir / "req-03.yaml.bak"
    bak_file.write_text(
        "req_id: req-03\ntitle: 测试需求\nstatus: done\ncreated: '2024-01-01'\n",
        encoding="utf-8",
    )
    assert bak_file.exists(), "sanity: .bak file should exist before install"

    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0, f"install_repo returned non-zero: {rc}"

    # 断言 .bak 文件已被删除
    assert not bak_file.exists(), (
        "req-03.yaml.bak should be deleted by cleanup_state_bak_files "
        "when matching .yaml exists; check install_repo calls cleanup_state_bak_files."
    )


def test_cleanup_state_bak_files_direct(tmp_path):
    """bugfix-4（harness install 升级清理）/ chg-2（state .bak 残留清理 helper）单元测试：
    直接调用 cleanup_state_bak_files，验证：
    - 有同名 .yaml 的 .bak 被删除并报告 'removed stale bak'
    - 无同名 .yaml 的 .bak 被保留并报告 'kept orphan bak'
    """
    state_dir = tmp_path / ".workflow" / "state" / "requirements"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Case 1: matching .yaml 存在
    yaml_a = state_dir / "req-01.yaml"
    bak_a = state_dir / "req-01.yaml.bak"
    yaml_a.write_text("id: req-01\n", encoding="utf-8")
    bak_a.write_text("req_id: req-01\n", encoding="utf-8")

    # Case 2: orphan .bak（无对应 .yaml）
    bak_b = state_dir / "req-99.yaml.bak"
    bak_b.write_text("req_id: req-99\n", encoding="utf-8")

    actions = cleanup_state_bak_files(tmp_path, check=False)

    # bak_a 应被删除
    assert not bak_a.exists(), "req-01.yaml.bak should be removed when req-01.yaml exists"
    # bak_b（orphan）应被保留
    assert bak_b.exists(), "req-99.yaml.bak should be kept when no matching .yaml exists"

    action_str = " ".join(actions)
    assert "removed stale bak" in action_str, f"Expected 'removed stale bak' in actions: {actions}"
    assert "kept orphan bak" in action_str, f"Expected 'kept orphan bak' in actions: {actions}"


def test_cleanup_state_bak_files_check_mode(tmp_path):
    """bugfix-4（harness install 升级清理）/ chg-2：check=True 时不实际删除。"""
    state_dir = tmp_path / ".workflow" / "state" / "requirements"
    state_dir.mkdir(parents=True, exist_ok=True)

    yaml_a = state_dir / "req-01.yaml"
    bak_a = state_dir / "req-01.yaml.bak"
    yaml_a.write_text("id: req-01\n", encoding="utf-8")
    bak_a.write_text("req_id: req-01\n", encoding="utf-8")

    actions = cleanup_state_bak_files(tmp_path, check=True)

    # check 模式下不删除
    assert bak_a.exists(), "check=True: .bak should NOT be deleted"
    action_str = " ".join(actions)
    assert "would remove" in action_str, f"Expected 'would remove' in check-mode actions: {actions}"


# ─────────────────────────────────────────────
# Fixture 3：req-XX/ folder 形态 → audit 警告，不删
# ─────────────────────────────────────────────

def test_schema_folder_audit_warning_not_deleted(tmp_path, monkeypatch, capsys):
    """bugfix-4（harness install 升级清理）/ chg-3（schema 探测扩 folder 形态 + audit 报告）：
    存量项目含 `req-06/`（folder schema，无对应 req-06.yaml），
    install_repo 后：
    - `req-06/` folder 仍然存在（不被删除，避免数据丢失）
    - install_repo 输出包含 '⚠️' audit 警告信息
    """
    monkeypatch.delenv("HARNESS_DEV_REPO_ROOT", raising=False)
    _git_init(tmp_path)

    req_state_dir = tmp_path / ".workflow" / "state" / "requirements"
    req_state_dir.mkdir(parents=True, exist_ok=True)

    # 模拟 legacy folder schema：req-06/ 内含旧报告文件，无对应 req-06.yaml
    folder_schema = req_state_dir / "req-06"
    folder_schema.mkdir(parents=True, exist_ok=True)
    (folder_schema / "testing-report.md").write_text(
        "# Testing Report\n\nreq-06 旧格式报告。\n",
        encoding="utf-8",
    )
    (folder_schema / "acceptance-report.md").write_text(
        "# Acceptance Report\n\nreq-06 验收报告。\n",
        encoding="utf-8",
    )
    # 确认无对应 .yaml
    assert not (req_state_dir / "req-06.yaml").exists(), (
        "sanity: req-06.yaml must NOT exist (simulating folder-schema legacy)"
    )

    rc = install_repo(tmp_path, force_skill=True, check=False)
    assert rc == 0, f"install_repo returned non-zero: {rc}"

    # 断言 folder 仍然存在（不删）
    assert folder_schema.exists(), (
        "req-06/ folder should NOT be deleted by install_repo "
        "(schema audit warns only, no data destruction)"
    )
    assert (folder_schema / "testing-report.md").exists(), (
        "testing-report.md inside req-06/ should be preserved"
    )

    # 断言 audit 警告输出到 stdout 或 stderr（通过 capsys）
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert "⚠️" in combined or "schema folder" in combined or "旧 schema" in combined, (
        f"Expected audit warning (⚠️ or 'schema folder') in output; got:\n"
        f"stdout={captured.out!r}\nstderr={captured.err!r}"
    )
