# Change

## 1. Title

工具层集成

## 2. Goal

在 tools 层集成 Claude Code 上下文管理，定义 `/compact`、`/clear`、`/new` 等命令在工作流中的规范用法：
- `tools/catalog/claude-code-context.md`：工具定义、用法、最佳实践
- `tools/stage-tools.md` 更新：各阶段可用的上下文管理工具
- `tools/selection-guide.md` 补充：何时使用哪些上下文维护动作

## 3. Requirement

- `req-04-上下文维护机制设计`

## 4. Scope

**包含**：
- 工具 catalog 条目创建：
  - `tools/catalog/claude-code-context.md`：完整定义 Claude Code 的上下文管理能力
  - 内容：命令列表（`/compact`、`/clear`、`/new`、`/help`）、用法示例、最佳实践
  - 与维护动作决策树（chg-02）的集成说明
- `tools/stage-tools.md` 更新：
  - 在各阶段工具白名单中添加上下文管理工具
  - 定义各阶段允许的上下文维护动作（如 testing 阶段可用 `/compact`，regression 阶段可用 `/clear`）
- `tools/selection-guide.md` 补充：
  - 增加上下文维护工具的选择指南
  - 根据上下文负载和阶段推荐合适的维护动作
- 工具使用经验沉淀模板：在 `context/experience/tool/` 下预留位置

**不包含**：
- 监控指标与阈值设计（属于 chg-01）
- 维护动作决策逻辑实现（属于 chg-02）
- handoff 交接协议具体内容（属于 chg-03）
- 风险与恢复路径的具体内容（属于 chg-05）
- 角色职责的具体更新（属于 chg-06）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`