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
    return install_repo(
        root,
        force_skill=False,
        check=args.check,
        force_managed=args.force_managed,
        force_all_platforms=args.all_platforms,
        agent_override=args.agent,
    )


if __name__ == "__main__":
    raise SystemExit(main())
