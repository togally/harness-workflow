"""路书骨架渲染（req-55（项目路书Playbook体系-项目地图+代码导航）/ chg-03（harness install 追加路书初始化））

按 playbook-layout.md §1-§4 生成路书骨架：
  - 4 顶层文件：overview.md / architecture.md / runbook.md / code-map.md
  - domains/{name}/：README.md / code.md / data-model.md / notes.md 4 件套

路径锁定 = {root}/artifacts/project/playbooks/（OQ-1=B）
各文件包含 <!-- AUTO:* --> 区段（§4 表 5 类标记），人工区留 TODO。
文件已存在不覆盖（幂等）。
"""
from __future__ import annotations

import sys
from pathlib import Path


PLAYBOOK_ROOT_SUFFIX = "artifacts/project/playbooks"

# 顶层文件模板 ------------------------------------------------------------------

_OVERVIEW_TEMPLATE = """\
# 项目概览地图

## 项目名称

<!-- TODO: 填写项目全名 -->

## 用途描述

<!-- LLM:OVERVIEW_DESC -->
<!-- TODO: ≤ 3 句话描述项目用途和目标用户 -->
<!-- /LLM:OVERVIEW_DESC -->

## 技术决策摘要

<!-- LLM:TECH_DECISIONS -->
<!-- TODO: 关键架构选型（语言 / 框架 / 存储），≤ 5 条 -->
<!-- /LLM:TECH_DECISIONS -->

## 活跃领域列表

<!-- AUTO:DOMAIN_LIST -->
<!-- /AUTO:DOMAIN_LIST -->

## 最近变更

<!-- TODO: 最近 3 次重要 req/bugfix 概述（human-authored，非 AUTO） -->
"""

_ARCHITECTURE_TEMPLATE = """\
# 架构总览

## 技术栈

<!-- AUTO:STACK -->
<!-- /AUTO:STACK -->

## 目录结构

<!-- AUTO:LAYOUT -->
<!-- /AUTO:LAYOUT -->

## 常用脚本

<!-- AUTO:SCRIPTS -->
<!-- /AUTO:SCRIPTS -->

## 组件关系

<!-- TODO: 人工描述子系统间调用关系 -->

## 关键依赖

<!-- TODO: 列主要三方依赖及其用途 -->
"""

_RUNBOOK_TEMPLATE = """\
# 运维操作手册入口

## 快速启动

<!-- TODO: 本地开发环境启动命令 -->

## 测试命令

<!-- TODO: 测试套件运行命令 -->

## 部署步骤

<!-- TODO: 生产 / 预发环境部署流程（按需）-->

## 常见问题排查

<!-- TODO: FAQ / troubleshooting guide（按需）-->
"""

_CODE_MAP_TEMPLATE = """\
# 代码结构地图

## 模块索引

<!-- AUTO:DOMAIN_FILES -->
<!-- /AUTO:DOMAIN_FILES -->

## 关键词索引

<!-- LLM:CODE_MAP_KEYWORDS -->
<!-- TODO: 项目级关键词（中英对照） -->
<!-- /LLM:CODE_MAP_KEYWORDS -->

## 入口文件

<!-- TODO: main / CLI 入口文件路径 + 一句话描述（human-authored）-->

## 配置文件

<!-- TODO: 关键配置文件路径 -->

## 测试目录

<!-- TODO: 测试文件位置约定 -->
"""

# 领域 4 件套模板 ---------------------------------------------------------------

def _domain_readme_template(domain_name: str) -> str:
    return f"""\
# 领域：{domain_name}

## 领域名称

{domain_name}

## 职责描述

<!-- LLM:DOMAIN_DESC -->
<!-- TODO: ≤ 3 句描述该领域处理什么业务 -->
<!-- /LLM:DOMAIN_DESC -->

## 关键词

<!-- LLM:KEYWORDS -->
<!-- TODO: 领域关键词（中英对照） -->
<!-- /LLM:KEYWORDS -->

## 关键文件

<!-- TODO: 该领域最重要的 2-3 个文件路径（human-authored）-->

## 依赖领域

<!-- TODO: 本领域依赖的其他领域（如有，可为空）-->
"""


def _domain_code_template(domain_name: str) -> str:
    return f"""\
# 领域代码清单：{domain_name}

## 文件列表

<!-- AUTO:DOMAIN_FILES -->
<!-- /AUTO:DOMAIN_FILES -->
"""


def _domain_data_model_template(domain_name: str) -> str:
    return f"""\
# 领域数据模型：{domain_name}

## 核心数据结构

<!-- TODO: 主要 class / struct / schema 名称 + 字段说明 -->

## 数据库表

<!-- TODO: 如适用：表名 + 主键 + 关键索引 + 用途 -->

## 数据流向

<!-- TODO: 数据创建 → 消费的简要流程（可选）-->
"""


def _domain_notes_template(domain_name: str) -> str:
    return f"""\
# 领域补充笔记：{domain_name}

## 跨领域笔记

<!-- TODO: 涉及本领域且从其他领域调用的流程说明 -->

## 待决策事项

<!-- TODO: 未解决的技术选型 / 架构问题（可选）-->

## 历史背景

<!-- TODO: 重要的架构决策历史（可选）-->
"""


# 渲染函数 ---------------------------------------------------------------------

def _write_if_absent(path: Path, content: str) -> bool:
    """文件不存在时写入；已存在则跳过（per-file 幂等）。返回是否实际写入。"""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def render_skeleton(root: Path, domains: list[str]) -> int:
    """生成路书骨架文件到 {root}/artifacts/project/playbooks/。

    返回写入文件数（0 = 全部已存在 / 幂等）。
    """
    root = Path(root).resolve()
    playbook_root = root / PLAYBOOK_ROOT_SUFFIX

    written = 0

    # 4 顶层文件
    top_files = [
        ("overview.md", _OVERVIEW_TEMPLATE),
        ("architecture.md", _ARCHITECTURE_TEMPLATE),
        ("runbook.md", _RUNBOOK_TEMPLATE),
        ("code-map.md", _CODE_MAP_TEMPLATE),
    ]
    for fname, template in top_files:
        if _write_if_absent(playbook_root / fname, template):
            print(f"[playbook] created {PLAYBOOK_ROOT_SUFFIX}/{fname}")
            written += 1

    # domains/{name}/ 4 件套
    for domain_name in domains:
        domain_dir = playbook_root / "domains" / domain_name
        domain_files = [
            ("README.md", _domain_readme_template(domain_name)),
            ("code.md", _domain_code_template(domain_name)),
            ("data-model.md", _domain_data_model_template(domain_name)),
            ("notes.md", _domain_notes_template(domain_name)),
        ]
        for fname, template in domain_files:
            if _write_if_absent(domain_dir / fname, template):
                print(f"[playbook] created {PLAYBOOK_ROOT_SUFFIX}/domains/{domain_name}/{fname}")
                written += 1

    return written
