"""init_playbook 主入口（req-56（路书引擎升级）/ chg-01（推断器多语言注册化）
兼容 req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-03（harness install 追加路书初始化））

init_playbook(root, skip=False, only=False, override_domains=None) -> int
  skip=True → 立即返回（--skip-playbook）
  only=True → 仅渲染骨架，跳 install_repo / install_agent（--playbook-only 由 cli 层处理）
  override_domains 非 None → 跳过推断器，直接用指定领域列表（--domains flag 透传）
  检查 artifacts/project/playbooks/ 已存在 → 跳过 + stdout 提示
  不存在 → 调 infer_domains(root, override_domains) + render_skeleton(root, domains)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from harness_workflow.playbook.domain_inference import infer_domains
from harness_workflow.playbook.skeleton import PLAYBOOK_ROOT_SUFFIX, render_skeleton


def init_playbook(
    root: Path,
    skip: bool = False,
    only: bool = False,
    override_domains: Optional[list[str]] = None,
) -> int:
    """初始化项目路书骨架。

    Args:
        root: 仓库根目录。
        skip: True → 立即返回 0（--skip-playbook 语义）。
        only: True → 仅渲染骨架（不跑 install_repo / install_agent；CLI 层保证调用顺序）。
        override_domains: 非 None → 跳过推断器，直接用指定领域列表（--domains flag 透传）。

    Returns:
        0 = 成功（包括跳过），1 = 失败。
    """
    root = Path(root).resolve()

    if skip:
        # --skip-playbook：不初始化路书
        return 0

    playbook_dir = root / PLAYBOOK_ROOT_SUFFIX

    # 已存在 → 跳过（幂等）
    if playbook_dir.exists() and any(playbook_dir.iterdir()):
        print("playbook 已存在，跳过初始化")
        return 0

    # 推断领域（透传 override_domains）
    matched_mode, domains = infer_domains(root, override_domains=override_domains)
    if not domains:
        print(
            "[playbook] WARN: 领域推断失败，路书初始化跳过。"
            "请手工创建 artifacts/project/playbooks/domains/ 结构。",
            file=sys.stderr,
        )
        # 返回 0（不阻塞 install 主流程；路书初始化软失败）
        return 0

    # 渲染骨架
    written = render_skeleton(root, domains)

    if written > 0:
        print(f"playbook initialized ({written} files created in {PLAYBOOK_ROOT_SUFFIX})")
    else:
        print("playbook 已存在，跳过初始化")

    return 0
