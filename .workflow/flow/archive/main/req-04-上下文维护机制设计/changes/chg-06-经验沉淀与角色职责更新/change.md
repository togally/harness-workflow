# Change

## 1. Title

经验沉淀与角色职责更新

## 2. Goal

沉淀本次上下文爆炸的教训并明确各角色在上下文维护中的职责：
- `context/experience/tool/claude-code.md` 或新文件记录教训
- 更新相关角色文件（主 agent、各阶段 subagent）中关于上下文维护的职责说明
- 在 `context/index.md` 加载顺序中增加上下文检查点（可选）

## 3. Requirement

- `req-04-上下文维护机制设计`

## 4. Scope

**包含**：
- 经验沉淀文件创建/更新：
  - `context/experience/tool/claude-code.md` 或新文件（如 `context/experience/stage/context-maintenance.md`）
  - 记录本次上下文爆炸的教训：现象、根因、解决方案
  - 记录上下文维护的最佳实践和常见错误
- 角色职责更新：
  - 主 agent 角色文件：增加上下文监控职责、维护动作触发职责
  - 各阶段 subagent 角色文件：增加上下文消耗报告职责、清理建议
  - 更新角色文件的 "职责外问题" 部分，包括上下文相关问题的上报
- `context/index.md` 加载顺序补充（可选）：
  - 在 Step 1 或 Step 5 增加上下文检查点
  - 如：在 before-task 时检查上下文负载，超阈值时提醒
- 与其他变更的集成：
  - 引用 chg-01 的监控指标和阈值
  - 引用 chg-02 的维护动作决策树
  - 引用 chg-04 的工具层集成

**不包含**：
- 监控指标与阈值设计的具体实现（属于 chg-01）
- 维护动作决策逻辑的具体实现（属于 chg-02）
- handoff 交接协议的具体内容（属于 chg-03）
- 工具层集成的具体实现（属于 chg-04）
- 风险与恢复路径的具体内容（属于 chg-05）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`