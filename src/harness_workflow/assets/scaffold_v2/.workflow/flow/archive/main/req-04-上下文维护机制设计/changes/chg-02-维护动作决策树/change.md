# Change

## 1. Title

维护动作决策树

## 2. Goal

设计维护动作决策逻辑，根据当前上下文负载和阈值，决定使用 `/compact`、`/clear` 还是新开 agent：
- `/compact` 适用场景：历史消息较多但仍有压缩空间，任务尚未完成
- `/clear` 适用场景：历史消息已无效或干扰，需要全新上下文
- 新开 agent 适用场景：上下文已爆满，需通过 `handoff.md` 交接继续任务

## 3. Requirement

- `req-04-上下文维护机制设计`

## 4. Scope

**包含**：
- 维护动作决策树设计：
  - 输入：当前上下文负载（token 估算百分比、消息条数等）
  - 决策逻辑：基于阈值选择维护动作
  - 输出：建议的维护动作（`/compact`、`/clear`、新开 agent）
- 各维护动作的适用场景详细定义：
  - `/compact`：何时使用、操作步骤、预期效果
  - `/clear`：何时使用、操作步骤、注意事项
  - 新开 agent：触发条件、交接要求、handoff 协议引用
- 决策树的实现形式：流程图、决策表或规则列表
- 与 chg-01 阈值设计的集成：引用预警、强制、紧急阈值

**不包含**：
- handoff 交接协议的具体内容（属于 chg-03）
- 工具层集成实现（属于 chg-04）
- 风险与恢复路径的具体内容（属于 chg-05）
- 角色职责的具体更新（属于 chg-06）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`