#!/usr/bin/env python3
"""Install harness skill to target agent directory.

chg-07（CLI 路由修正：harness install 接 install_repo + 移除 harness update --flag
的 install_repo hack）：在 `install_agent` 之后追加 `install_repo` 调用，让
`harness install` 成为同步契约的唯一真入口（reg-02 根因 A）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from harness_workflow.workflow_helpers import install_agent, install_repo


def _print_venv_check() -> int:
    """输出 venv mtime vs HEAD commit ts 差值（sug-55（chg-02 部署同步契约 dev mode flag）配套）。

    输出格式（不强制重装）：
        [install --check] venv_mtime=<float> HEAD_commit_ts=<float> diff=<float>s
        [install --check] WARN: venv is older than HEAD commit  （若 diff < 0）
        [install --check] OK: venv is up-to-date  （若 diff >= 0）

    Returns:
        0 = 无问题（diff >= 0）；1 = venv 较 HEAD 旧（diff < 0）。

    req-47（整合清理所有 suggest，先判断当前版本适用性，再将清理后建议打包开发）/
    chg-01（testing 红线 + safer dogfood + commit revert dry-run）落地 sug-55（chg-02 部署同步契约 dev mode flag）。
    """
    import os
    import subprocess

    venv_mtime: float = -1.0
    head_commit_ts: float = -1.0

    # 获取 venv workflow_helpers.py mtime
    try:
        import harness_workflow.workflow_helpers as _wh_mod
        venv_mtime = os.path.getmtime(_wh_mod.__file__)
        print(f"[install --check] _is_stage_work_done import OK: {_wh_mod.__file__}")
    except Exception as exc:
        print(f"[install --check] WARN: cannot import harness_workflow.workflow_helpers: {exc}", file=sys.stderr)

    # 获取 HEAD commit ts（workflow_helpers.py 最新修改时间）
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", "src/harness_workflow/workflow_helpers.py"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            head_commit_ts = float(result.stdout.strip())
    except Exception:
        pass

    if venv_mtime >= 0 and head_commit_ts >= 0:
        diff = venv_mtime - head_commit_ts
        print(f"[install --check] venv_mtime={venv_mtime:.0f} HEAD_commit_ts={head_commit_ts:.0f} diff={diff:.0f}s")
        if diff < 0:
            print("[install --check] WARN: venv is older than HEAD commit — consider running 'harness install'", file=sys.stderr)
            return 1
        print("[install --check] OK: venv is up-to-date")
    else:
        print(f"[install --check] venv_mtime={venv_mtime:.0f} HEAD_commit_ts={head_commit_ts:.0f} (partial data)")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install harness skill to target agent directory.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--agent", required=True, help="Target agent (kimi, claude, codex, qoder).")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Show what would change without writing files (dry-run, transparent to install_repo).",
    )
    parser.add_argument(
        "--force-managed",
        action="store_true",
        help="Overwrite managed files even if they were modified locally (transparent to install_repo).",
    )
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Refresh all agents/platforms (compatibility escape hatch; overrides active_agent).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    # 1) install_agent：写入 agent 配置 + skill 文件
    rc = install_agent(root, args.agent)
    if rc != 0:
        return rc
    # 2) install_repo：同步契约的真入口（reg-02 根因 A 收口）
    rc = install_repo(
        root,
        force_skill=False,
        check=args.check,
        force_managed=args.force_managed,
        force_all_platforms=args.all_platforms,
        agent_override=args.agent,
    )
    # 3) check 模式：追加 venv mtime 版本对比报告（sug-55 配套）
    if args.check:
        _print_venv_check()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
