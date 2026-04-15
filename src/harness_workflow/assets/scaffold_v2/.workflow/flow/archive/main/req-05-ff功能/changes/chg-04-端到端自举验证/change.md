# Change: chg-04

## Title

端到端自举验证与经验沉淀

## Goal

使用增强后的 ff 模式完成 req-05 自身的完整流程（从 requirement_review 到 archive），验证 ff 模式的可行性，记录实际问题和改进点，并沉淀 skill 缺失处理与平台错误恢复的经验。

## Scope

**包含**：
- 在 chg-01~chg-03 完成后，尝试用 ff 模式走完 req-05 的剩余阶段
- 验证所有文件产出完整（change.md、plan.md、代码/文档变更、session-memory、done 报告等）
- 记录 ff 模式执行过程中的问题和经验教训
- 更新 `context/experience/stage/` 或 `context/experience/tool/` 下的经验文件
- 沉淀本次 regression 中发现的"skill 缺失处理"和"平台错误恢复"经验教训

**不包含**：
- 在 chg-01~chg-03 完成前就开始执行验证
- 修改验证范围外的其他需求

## Acceptance Criteria

- [ ] req-05 能够从当前状态通过 ff 模式走到 archive
- [ ] 所有 stage 的必须产出都已存在且完整
- [ ] `session-memory.md` 记录了 ff 执行过程
- [ ] 经验文件已更新（至少包含 ff 模式、skill 缺失处理、平台错误恢复三类经验之一）
