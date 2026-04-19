# Requirement

## 1. Title

上下文维护机制设计

## 2. Goal

用户触发 Claude API 上下文长度超限（102400 tokens），询问上下文处理机制、`/compact`/`/clear` 命令使用时机、新启 agent 的执行条件。

当前工作流系统缺乏明确的上下文维护机制，导致：
- 原则与实现脱节：`project-overview.md` 实践原则第 1 条写明 "上下文爆满时不压缩：新开 agent，通过 handoff.md 交接"，但 `handoff.md` 不存在，交接机制未实现
- 工具层缺失策略：未定义何时使用 Claude Code 内置命令 (`/compact`、`/clear`)，无自动监控
- 状态层未跟踪负载：`state/` 未记录会话长度、token 估算等指标
- 职责不明确：主 agent 是否应主动监控？用户何时应手动干预？

本需求的目标：**设计上下文维护机制**，定义明确的监控指标、触发阈值、维护动作和交接协议，避免上下文爆炸导致工作流中断。

## 3. Scope

**包含**：
- **监控指标定义**：token 估算方法、消息条数、文件读取量、会话时长等可量化指标
- **触发阈值设计**：预警阈值（如 80% 最大上下文）、强制维护阈值（如 90%）、不同阈值对应的维护动作
- **维护动作清单**：
  - Claude Code 内置命令使用规范：`/compact`（压缩历史）、`/clear`（清除历史）的适用场景和操作步骤
  - 新开 agent 交接协议：`handoff.md` 文件格式、交接内容（上下文摘要、待处理问题、下一步任务）
  - 各角色职责：主 agent 监控职责、subagent 清理义务、用户手动干预时机
- **工具层集成**：在 `tools/catalog/` 增加 Claude Code 上下文管理工具条目，定义其用法和最佳实践
- **风险与恢复**：在 `constraints/risk.md` 增加上下文爆炸的风险条目，在 `constraints/recovery.md` 增加恢复路径
- **经验沉淀**：在 `context/experience/stage/` 或 `context/experience/tool/` 下记录本次教训和应对策略

**不包含**：
- 实时自动监控系统的实现（属于后续技术实现需求）
- Claude Code 客户端修改或插件开发
- 改变 Claude API 的上下文长度限制
- 修改现有阶段角色文件的核心职责（只增加上下文维护相关的补充职责）

## 4. Acceptance Criteria

- **设计文档**：`req-04/design.md` 完整定义上下文维护机制，包含：
  - 监控指标及其量化方法
  - 触发阈值（至少两个级别：预警、强制）
  - 维护动作决策树（根据阈值选择 `/compact`、`/clear` 或新开 agent）
  - `handoff.md` 交接协议模板
  - 各角色在上下文维护中的职责分工
- **工具集成**：`tools/catalog/claude-code-context.md` 存在，描述 Claude Code 的 `/compact`、`/clear`、`/new` 等命令在工作流中的规范用法
- **风险注册**：`constraints/risk.md` 新增 "上下文爆炸导致工作流中断" 风险条目，包含场景、影响和缓解措施
- **恢复路径**：`constraints/recovery.md` 新增上下文超限后的恢复步骤
- **经验沉淀**：`context/experience/tool/claude-code.md` 或类似位置记录本次上下文爆炸的教训和应对经验

## 5. Split Rules

### chg-01 监控指标与阈值设计

定义上下文维护的监控指标和触发阈值：
- 指标：token 估算（基于消息历史、文件内容）、消息条数、文件读取次数、会话时长
- 阈值：预警阈值（如 70-80%）、强制维护阈值（如 85-90%）、紧急阈值（>95%）
- 指标采集方法：主 agent 定期估算、subagent 任务结束报告、用户手动检查点

### chg-02 维护动作决策树

设计维护动作决策逻辑：
- 根据当前上下文负载和阈值，决定使用 `/compact`、`/clear` 还是新开 agent
- `/compact` 适用场景：历史消息较多但仍有压缩空间，任务尚未完成
- `/clear` 适用场景：历史消息已无效或干扰，需要全新上下文
- 新开 agent 适用场景：上下文已爆满，需通过 `handoff.md` 交接继续任务

### chg-03 handoff 交接协议

创建 `handoff.md` 协议模板：
- 上下文摘要：当前任务状态、关键决策、待处理问题
- 交接内容：必须传递的文件、状态、会话记忆片段
- 接收方指引：下一步动作、注意事项、风险提示
- 格式规范：Markdown 结构、必填字段、示例

### chg-04 工具层集成

在 tools 层集成 Claude Code 上下文管理：
- `tools/catalog/claude-code-context.md`：工具定义、用法、最佳实践
- `tools/stage-tools.md` 更新：各阶段可用的上下文管理工具
- `tools/selection-guide.md` 补充：何时使用哪些上下文维护动作

### chg-05 风险与恢复路径

在 constraints 层注册风险并定义恢复路径：
- `constraints/risk.md` 新增条目
- `constraints/recovery.md` 新增恢复步骤
- 更新 `constraints/boundaries.md` 中与上下文相关的行为边界

### chg-06 经验沉淀与角色职责更新

沉淀本次经验并明确各角色职责：
- `context/experience/tool/claude-code.md` 或新文件记录教训
- 更新相关角色文件（主 agent、各阶段 subagent）中关于上下文维护的职责说明
- 在 `context/index.md` 加载顺序中增加上下文检查点（可选）