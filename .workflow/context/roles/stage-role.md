# Stage 角色公共规约（stage-role）

本文件继承 `.workflow/context/roles/base-role.md` 的通用规约，是所有 **stage 执行角色**（requirement-review、planning、executing、testing、acceptance、regression、done）和 **辅助角色**（toolsManager）的公共父类。

加载顺序：`base-role.md → stage-role.md → {具体角色}.md`

## Session Start 约定

每个 stage 角色被加载时，应默认已完成以下前置加载：
1. `runtime.yaml` 已被读取
2. `base-role.md` 已被读取
3. `stage-role.md` 已被读取
4. 本 stage 角色文件正在被读取
5. （若适用）对应的经验文件和评估文件已被加载

subagent 不需要重复读取 `runtime.yaml`、`base-role.md` 或 `stage-role.md`，除非任务明确要求。

## Stage 切换上下文交接约定

当从一个 stage 推进到下一个 stage 时：
1. 原 stage 的 subagent 应确认关键决策和进度已保存到 `session-memory.md`
2. 主 agent（技术总监）负责更新 `runtime.yaml` 到目标 stage
3. 新 stage 的 subagent 应首先读取 `session-memory.md` 了解已完成的工作
4. 上下文负载达到强制维护阈值时，优先执行维护动作再加载新 stage

## 经验文件加载规则

subagent 在被主 agent 派发任务后，除读取本 stage 特有文档外，还应按以下约定加载必要的共享上下文：

### 按角色加载经验文件
- 读取 `.workflow/state/experience/index.md` 获取加载规则
- 按当前角色名加载对应经验文件（路径为 `context/experience/roles/{角色名}.md`）：
  - `requirement-review` → `context/experience/roles/requirement-review.md`
  - `planning` → `context/experience/roles/planning.md`
  - `executing` → `context/experience/roles/executing.md`
  - `testing` → `context/experience/roles/testing.md`
  - `acceptance` → `context/experience/roles/acceptance.md`
  - `regression` → `context/experience/roles/regression.md`
  - `done` → 不强制加载特定经验文件，但可加载同阶段相关经验
  - `toolsManager` → `context/experience/tool/` 下相关工具经验
- **不得批量加载整棵经验目录树**，只加载与当前角色匹配的分类

### 团队与项目上下文（before-task）
- 在开始实质性任务（生成代码、修改文件、制定计划）前加载：
  - `.workflow/context/team/development-standards.md`：团队开发规范、代码风格约束

### 风险文件（before-task 必须）
- 读取 `.workflow/constraints/risk.md`，扫描高风险关键词
- 约束文件层级参考 `.workflow/constraints/index.md`：
  - `constraints/boundaries.md`：行为边界细则（before-task 时按需加载）
  - `constraints/risk.md`：风险扫描规则（before-task 必须执行）
  - `constraints/recovery.md`：失败恢复路径（遇到失败时加载）

## 流转规则（按需）

- 如需判断 stage 推进条件或归档规则，读取 `.workflow/flow/stages.md`
- stage 角色只关心本角色的进入条件、退出条件和必须产出
- 全局 stage 流转的守护职责由顶级角色（技术总监）承担
