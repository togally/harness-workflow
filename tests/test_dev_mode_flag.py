"""TC-06 / TC-07：HARNESS_DEV_MODE=1 dev mode flag 测试用例。

req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地
sug-55（chg-02 部署同步契约 dev mode flag）。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_tc06_harness_dev_mode_1_deployment_sync_pass(tmp_path: Path) -> None:
    """TC-06：HARNESS_DEV_MODE=1 → deployment-sync 检查豁免 → exit 0。"""
    # 创建最小 .workflow 骨架
    (tmp_path / ".workflow" / "state").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["HARNESS_DEV_MODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "deployment-sync", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, (
        f"Expected exit 0 with HARNESS_DEV_MODE=1, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "dev mode" in combined.lower() or "HARNESS_DEV_MODE" in combined, (
        f"Expected dev mode notice in output:\n{combined}"
    )


def test_tc07_no_dev_mode_strict_check(tmp_path: Path) -> None:
    """TC-07：不设 HARNESS_DEV_MODE → 严格模式 → import 验证（exit 0 if import OK）。"""
    (tmp_path / ".workflow" / "state").mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.pop("HARNESS_DEV_MODE", None)  # 确保未设
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "validate",
         "--contract", "deployment-sync", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    # 严格模式：import 验证通过 → exit 0
    assert result.returncode == 0, (
        f"Expected exit 0 in strict mode (import OK), got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "strict" in combined.lower() or "import OK" in combined or "严格模式" in combined, (
        f"Expected strict mode notice in output:\n{combined}"
    )


def test_tc09_install_check_outputs_mtime(tmp_path: Path) -> None:
    """TC-09（部分）：harness install --check 输出 venv mtime 相关信息 + exit 0/1（不修改文件）。

    注：install --check 需要 --agent 参数；实测用 claude agent 跑。
    """
    result = subprocess.run(
        [sys.executable, "-m", "harness_workflow.cli", "install",
         "--check", "--agent", "claude", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    # install --check 不应报 unknown command
    assert "error: unrecognized" not in combined.lower(), (
        f"install --check should not report unrecognized args:\n{combined}"
    )
    # venv mtime 检查：输出应含 venv_mtime 或 install --check 相关关键字
    # （函数在 check 模式追加输出）
    assert "install --check" in combined or "venv_mtime" in combined or "mtime" in combined.lower(), (
        f"Expected venv mtime output in install --check:\n{combined}"
    )
