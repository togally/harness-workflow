# Change

## 1. Title

风险与恢复路径

## 2. Goal

在 constraints 层注册上下文爆炸风险并定义恢复路径：
- `constraints/risk.md` 新增 "上下文爆炸导致工作流中断" 风险条目
- `constraints/recovery.md` 新增上下文超限后的恢复步骤
- 更新 `constraints/boundaries.md` 中与上下文相关的行为边界

## 3. Requirement

- `req-04-上下文维护机制设计`

## 4. Scope

**包含**：
- 风险条目注册：
  - `constraints/risk.md` 新增风险条目 "上下文爆炸导致工作流中断"
  - 风险描述：上下文长度超限导致 API 调用失败、工作流中断
  - 影响：会话丢失、任务中断、需要重新开始
  - 缓解措施：引用本需求设计的监控指标、阈值、维护动作
- 恢复路径设计：
  - `constraints/recovery.md` 新增 "上下文超限恢复" 章节
  - 恢复步骤：检测超限、执行维护动作、恢复工作流、验证完整性
  - 与 handoff 协议（chg-03）的集成
- 行为边界更新：
  - `constraints/boundaries.md` 增加与上下文维护相关的行为边界
  - 如：主 agent 应定期监控上下文负载、subagent 应报告上下文消耗等
- 与其他变更的集成：
  - 引用 chg-01 的监控指标和阈值
  - 引用 chg-02 的维护动作决策树
  - 引用 chg-03 的 handoff 交接协议

**不包含**：
- 监控指标与阈值设计的具体实现（属于 chg-01）
- 维护动作决策逻辑的具体实现（属于 chg-02）
- handoff 交接协议的具体内容（属于 chg-03）
- 工具层集成的具体实现（属于 chg-04）
- 经验沉淀与角色职责的具体更新（属于 chg-06）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`