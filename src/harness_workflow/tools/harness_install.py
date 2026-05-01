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
from harness_workflow.playbook.init import init_playbook


def _print_venv_check() -> int:
    """输出 venv 安装源 commit_id + 本地 HEAD commit + diff hint（bugfix-7 / chg-01 Fix-B）。

    输出格式（stdout）：
        [install --check] venv installed from: <commit_id>（来自 direct_url.json 或 pipx_metadata.json）
        [install --check] local repo HEAD: <head_commit>（来自 git log -1 --format=%H）
        [install --check] OK: venv is up-to-date  （venv_commit == HEAD）
        [install --check] WARN: venv X commits behind HEAD  （venv_commit 落后于 HEAD）

    不依赖 venv 内含 helper（CLI 子进程独立跑 git log）；旧版 venv 也能跑。

    Returns:
        0 = venv 与 HEAD 一致或无法对比；1 = venv 明确落后于 HEAD。
    """
    import glob
    import json
    import os
    import subprocess

    venv_commit: str = ""
    head_commit: str = ""

    # 1) 从 direct_url.json 获取 venv 安装源 commit_id（bugfix-7 Fix-B 主路径）
    # 路径：~/.local/pipx/venvs/harness-workflow/lib/python*/site-packages/harness_workflow-*.dist-info/direct_url.json
    try:
        home = os.path.expanduser("~")
        pattern = os.path.join(
            home, ".local", "pipx", "venvs", "harness-workflow",
            "lib", "python*", "site-packages", "harness_workflow-*.dist-info", "direct_url.json"
        )
        matches = glob.glob(pattern)
        if matches:
            data = json.loads(Path(matches[0]).read_text(encoding="utf-8"))
            venv_commit = data.get("vcs_info", {}).get("commit_id", "")
    except Exception:
        pass

    # 2) 回退：从 pipx_metadata.json 获取（兼容不同 pipx 版本）
    if not venv_commit:
        try:
            meta_path = os.path.join(
                os.path.expanduser("~"), ".local", "pipx", "venvs",
                "harness-workflow", "pipx_metadata.json"
            )
            if os.path.exists(meta_path):
                meta = json.loads(Path(meta_path).read_text(encoding="utf-8"))
                # pipx_metadata.json 存结构各版本略有不同，尝试几个路径
                pkg = meta.get("main_package", {})
                venv_commit = (
                    pkg.get("vcs_info", {}).get("commit_id", "")
                    or pkg.get("package_version", "")
                )
        except Exception:
            pass

    # 3) 兜底：从 venv workflow_helpers.py mtime 推算（旧行为保留）
    venv_mtime: float = -1.0
    if not venv_commit:
        try:
            import harness_workflow.workflow_helpers as _wh_mod
            venv_mtime = os.path.getmtime(_wh_mod.__file__)
        except Exception as exc:
            print(f"[install --check] WARN: cannot import harness_workflow.workflow_helpers: {exc}", file=sys.stderr)

    # 4) 获取本地 repo HEAD commit（git log -1 --format=%H，子进程独立跑，不依赖 venv）
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            head_commit = result.stdout.strip()
    except Exception:
        pass

    # 5) 输出对比报告（stdout）
    if venv_commit:
        print(f"[install --check] venv installed from: {venv_commit}")
    elif venv_mtime >= 0:
        print(f"[install --check] venv_mtime={venv_mtime:.0f} (direct_url.json not found; fallback to mtime)")
    else:
        print("[install --check] venv commit: unknown (pipx metadata not found)")

    if head_commit:
        print(f"[install --check] local repo HEAD: {head_commit}")
    else:
        print("[install --check] local repo HEAD: unknown (git not available)")

    # 6) 计算 diff hint
    if venv_commit and head_commit:
        if venv_commit == head_commit:
            print("[install --check] OK: venv is up-to-date")
            return 0
        # git log venv_commit..HEAD 统计落后 commit 数
        try:
            diff_result = subprocess.run(
                ["git", "log", f"{venv_commit}..{head_commit}", "--oneline"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if diff_result.returncode == 0:
                behind_lines = [l for l in diff_result.stdout.strip().splitlines() if l]
                behind_count = len(behind_lines)
                if behind_count > 0:
                    print(
                        f"[install --check] WARN: venv {behind_count} commit(s) behind HEAD "
                        f"— push changes then 'pipx reinstall harness-workflow'",
                        file=sys.stderr,
                    )
                    return 1
                # venv_commit 不在 HEAD 祖先链（非线性历史）
                print("[install --check] WARN: venv commit not in local history (diverged or force-pushed)", file=sys.stderr)
                return 1
        except Exception:
            pass
        print(f"[install --check] WARN: venv commit ({venv_commit[:8]}) differs from HEAD ({head_commit[:8]})", file=sys.stderr)
        return 1
    elif venv_mtime >= 0 and head_commit:
        # 兜底：mtime 对比
        try:
            ts_result = subprocess.run(
                ["git", "log", "-1", "--format=%ct", "--", "src/harness_workflow/workflow_helpers.py"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if ts_result.returncode == 0 and ts_result.stdout.strip():
                head_commit_ts = float(ts_result.stdout.strip())
                diff = venv_mtime - head_commit_ts
                print(f"[install --check] venv_mtime={venv_mtime:.0f} HEAD_commit_ts={head_commit_ts:.0f} diff={diff:.0f}s")
                if diff < 0:
                    print("[install --check] WARN: venv is older than HEAD commit — consider running 'harness install'", file=sys.stderr)
                    return 1
                print("[install --check] OK: venv is up-to-date (mtime check)")
                return 0
        except Exception:
            pass

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install harness skill to target agent directory.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--agent", required=True, help="Target agent (cc, claude, codex).")
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
    # chg-D（精简命令体系）：删除 --skip-playbook / --playbook-only 两个 flag。
    # 路书骨架是 1.0.0 标配，install 始终装路书（无选项）。
    # req-56（路书引擎升级）/ chg-01（推断器多语言注册化）：
    # --domains：逗号分隔的领域列表，跳过推断器直接用用户指定领域（last-resort escape hatch）。
    parser.add_argument(
        "--domains",
        dest="domains",
        default=None,
        help="Comma-separated domain names, bypassing domain inference (e.g. --domains a,b,c).",
    )
    # req-56（路书引擎升级）/ chg-04（install/refresh 集成 LLM）：
    parser.add_argument(
        "--no-llm",
        dest="no_llm",
        action="store_true",
        help="Skip LLM content filling stage (also auto-skipped when CI=true).",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()

    no_llm = getattr(args, "no_llm", False)
    # 解析 --domains flag 为列表
    override_domains = None
    if getattr(args, "domains", None):
        override_domains = [d.strip() for d in args.domains.split(",") if d.strip()]

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
    if rc != 0:
        return rc
    # 4) init_playbook：追加路书初始化阶段（chg-D：始终装路书骨架，不输出 ASSISTANT INSTRUCTION 提示句）
    return init_playbook(root, override_domains=override_domains, no_llm=no_llm)


if __name__ == "__main__":
    raise SystemExit(main())
