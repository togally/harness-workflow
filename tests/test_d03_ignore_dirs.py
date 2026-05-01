"""tests/test_d03_ignore_dirs.py

chg-F bug-2：D-03 检测器用 IGNORE_DIRS（logs/build/target 不误报）

TC-01: logs/ 目录不被 D-03 报为 module dir drift
TC-02: target/ 和 build/ 目录不被 D-03 报
TC-03: 正常源码模块仍被 D-03 报（未在 domains/ 中登记时）
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = str(REPO_ROOT / "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from harness_workflow.tools.harness_playbook_check import check_d03_module_dir_drift


def _make_playbook_root(root: Path, existing_domains: list[str] | None = None) -> Path:
    """创建 artifacts/project/playbooks/domains/ 结构。"""
    pb_root = root / "artifacts" / "project" / "playbooks"
    domains_dir = pb_root / "domains"
    domains_dir.mkdir(parents=True, exist_ok=True)
    if existing_domains:
        for d in existing_domains:
            (domains_dir / d).mkdir(exist_ok=True)
    return pb_root


# ---------------------------------------------------------------------------
# TC-01: logs/ 目录不被 D-03 报
# ---------------------------------------------------------------------------

def test_tc01_logs_not_reported_by_d03(tmp_path):
    """TC-01: src/{pkg}/logs/ 不被 D-03 报为 module dir drift。"""
    # 建 src/myapp/logs/（IGNORE_DIRS 成员）
    (tmp_path / "src" / "myapp" / "logs").mkdir(parents=True)

    # domains/ 空（无对应）
    pb_root = _make_playbook_root(tmp_path)

    result = check_d03_module_dir_drift(tmp_path, pb_root)
    drift_modules = [issue for issue in result.issues if "'logs'" in issue]
    assert len(drift_modules) == 0, (
        f"logs/ should NOT be reported by D-03, but got: {drift_modules}"
    )


# ---------------------------------------------------------------------------
# TC-02: target/ 和 build/ 目录不被 D-03 报
# ---------------------------------------------------------------------------

def test_tc02_target_build_not_reported_by_d03(tmp_path):
    """TC-02: src/{pkg}/target/ + src/{pkg}/build/ 不被 D-03 报。"""
    pkg_dir = tmp_path / "src" / "javaapp"
    for noise_dir in ["target", "build"]:
        (pkg_dir / noise_dir).mkdir(parents=True, exist_ok=True)

    pb_root = _make_playbook_root(tmp_path)

    result = check_d03_module_dir_drift(tmp_path, pb_root)

    for noise in ["target", "build"]:
        matching = [issue for issue in result.issues if f"'{noise}'" in issue]
        assert len(matching) == 0, (
            f"{noise}/ should NOT be reported by D-03, but got: {matching}"
        )


# ---------------------------------------------------------------------------
# TC-03: 正常源码模块仍被 D-03 报（未在 domains/ 登记）
# ---------------------------------------------------------------------------

def test_tc03_real_module_still_reported(tmp_path):
    """TC-03: src/{pkg}/payment/ 不在 IGNORE_DIRS + 不在 domains/ → D-03 仍报。"""
    pkg_dir = tmp_path / "src" / "shop"
    # 正常模块（不在 IGNORE_DIRS 中）
    (pkg_dir / "payment").mkdir(parents=True)

    # domains/ 不含 payment
    pb_root = _make_playbook_root(tmp_path, existing_domains=["order"])

    result = check_d03_module_dir_drift(tmp_path, pb_root)
    matching = [issue for issue in result.issues if "'payment'" in issue]
    assert len(matching) >= 1, (
        f"payment/ should be reported by D-03 when not in domains/, but got no issues. "
        f"All issues: {result.issues}"
    )
