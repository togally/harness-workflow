# Regression Decision — req-25-6-p0

## 1. Decision Status

- **confirmed**（6/6 P0 全部确认，0 项误判）

## 2. Final Notes

### 核查结论
- P0-01 ~ P0-06 均为真实阻断性缺陷，根因全部定位至 `src/harness_workflow/` 内
- 无需人工补充信息；无需升级为新 requirement
- 所有修复均在 req-25 当前周期内可收口

### 分组依据
三项共同根因 **req-27 路径迁移未收口** 的问题（P0-03/04/05），合并为一个 change；其余三项（P0-01/02/06）根因相互独立，各自走 bugfix。

---

## 3. Follow-Up

### 推荐路由决策（按建议执行顺序）

| # | 组 | 类型 | 标题 | 建议命令 | 主要修改点 |
|---|---|---|---|---|---|
| 1 | A | change | 完成 req-27 遗留的 requirement 路径迁移 | `harness change "完成 requirement 路径迁移到 artifacts/{branch}"` | `workflow_helpers.py` 的 `3134 / 3377 / 3530 / 3562 / 3782 / 3830 / 3897`（+ 相关 archive_base 目标路径）从 `.workflow/flow/requirements` 全部改为 `artifacts/{branch}/requirements`；建议抽公共 helper `resolve_requirement_root(root) -> Path` 统一来源 |
| 2 | B | bugfix | install 在空仓应自动 init | `harness bugfix "install 在空仓自动 init"` | `workflow_helpers.py:4173` `install_agent` 前置检查改为：若 `.workflow` 缺失则先内联调用 `init_repo`，然后继续；或在 `cli.py:263` 层前置 `init_repo` 调用 |
| 3 | C | bugfix | scaffold_v2 清洗自身历史数据 | `harness bugfix "scaffold 清洗 harness-workflow 历史数据"` | 物理清洗 `src/harness_workflow/assets/scaffold_v2/`：删除 `.workflow/state/sessions/req-*`、`.workflow/flow/archive/`、`.workflow/flow/suggestions/archive/`、`.workflow/flow/requirements/req-25-.../`、`.workflow/archive/`；重写 `runtime.yaml` 为初始空白态（`current_requirement: ""`, `stage: "requirement_review"`, `ff_mode: false`, `active_requirements: []`）；加 MANIFEST/打包时过滤，防止再次泄漏 |
| 4 | D | bugfix | install --agent kimi 产出缺失 + install_agent delete 未执行 | `harness bugfix "install --agent 模板一致性"` | ①统一 `get_skill_template_root` 与 `SKILL_ROOT` 为单一模板源（建议合并到 `assets/skill/`）；②`_project_skill_targets:1974` 移除 kimi 跳过或补齐 kimi 分支；③`install_agent:4184-4229` 的 changes 循环必须执行 delete/modify，或改为 dry-run + 二次 apply 的清晰流程 |

### 建议执行顺序
1. 先执行 A 组 change（路径迁移） — 因为它会让 archive/validate/rename 三条命令同时复活，是最大 ROI
2. 然后 B 组 bugfix（install 空仓） — 新用户入口
3. C 组 bugfix（scaffold 清洗） — 修完后建议重跑回归，scaffold_v2 清洗可能影响 init 测试
4. 最后 D 组 bugfix（kimi + install_agent 一致性）— 独立隔离，可并行

### 不升级为 requirement 的理由
- 6 项均是"既定设计的实现缺陷"而非新需求，边界清晰、无需求分析
- req-27 的设计意图（artifacts 根目录重构）已经明确，A 组仅补完未迁移的代码
- B/C/D 组都是单文件级别的局部修复

### 不建议延期的项
- 6 项全部不延期。上游 req-25 的 acceptance criteria 4（四 agent 一致）和 acceptance criteria 主路径（install→requirement→change→archive 闭环）必须在本 req 内修复

### 人工输入需求
- **无**（`required-inputs.md` 保持空白即可）

