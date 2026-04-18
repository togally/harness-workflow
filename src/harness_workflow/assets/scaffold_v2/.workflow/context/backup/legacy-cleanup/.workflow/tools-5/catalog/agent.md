# 工具：Agent

**类型：** 内置工具
**状态：** active

## 适用场景
- 主 agent 派发节点任务给 subagent
- 需要独立视角执行的任务（测试、验收、诊断）
- context 爆满时交接工作给新 agent

## 不适用场景
- 简单的文件读写操作（直接用 Read/Edit 更快）
- 主 agent 自身的状态管理操作

## 推荐 prompt 模式

| 任务类型 | 调用要点 |
|---------|---------|
| 执行节点任务 | briefing = 角色文件 + change.md + plan.md + session-memory |
| 独立评估 | briefing = 角色文件 + requirement.md + 不含执行过程的上下文 |
| context 交接 | briefing = handoff.md 全文 |

## 注意事项
- subagent 启动时无对话历史，briefing 必须完整自包含
- subagent 完成后主 agent 必须执行状态回流（更新 session-memory + state）
- 生产者和评估者必须是不同的 agent 实例

## 迭代记录
