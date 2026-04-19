# Change: chg-02

## Title
对话摘要读取与展示

## Goal
在用户 `harness enter` 或有活跃需求时，自动读取并展示最近一次的 session-memory 摘要。

## Scope

**包含**：
- 修改 `harness enter` 或相关入口逻辑，读取当前 req 的 `session-memory.md`
- 提取 `## Stage 结果摘要` 内容并打印到 CLI
- 更新 `enter` 命令的帮助说明

**不包含**：
- 修改 enter 的核心流程（仅增加展示逻辑）
- 外部存储集成

## Acceptance Criteria

- [ ] `harness enter` 时，如果有当前 req 的 session-memory，打印其摘要
- [ ] 如果没有 session-memory，给出友好提示
- [ ] CLI 帮助或文档已更新
