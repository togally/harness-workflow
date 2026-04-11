# Version Memory

## 1. Current Goal

让 harness 管理的项目"越用越聪明"——应用项目积累业务经验，工具项目积累流程优化经验，两条线各自闭环。

## 2. Current Status

### 已交付

| # | Change | 状态 | 成果 |
|---|--------|------|------|
| 1 | 现有能力审计与测试补全 | ✅ | 从 20 个测试增加到 49 个，覆盖全部 19 条命令 |
| 2 | 已知缺陷修复 | ✅ | 修复 lint 脚本硬编码中文路径和旧版目录结构 |
| 3 | 自进化规范设计 | ✅ | 完整的 experience 生命周期文档：采集→升级→沉淀→淘汰 |
| 4 | 工具反馈回流设计与实现 | ✅ | `harness feedback` 命令 + 事件采集 + JSON 输出 |
| 5 | 自进化核心实现 | ✅ | feedback 事件嵌入 ff/next/regression 命令 |
| 6 | 工具项目自优化规范设计 | ✅ | 三级通道规格 + 聚合规则 + 优化提案机制 |
| 7 | MCP 能力索引与决策链 | ✅ | mcp-registry + mcp-catalog 模板 + before-human-input hook |

### 关键决策

- feedback 数据先输出到本地 JSON，格式兼容未来 MCP/curl
- MCP catalog 采用 triggers 关键词匹配机制
- 经验置信度采用 hit_count 驱动的三级升级（low→medium→high）
- lint 脚本统一使用英文路径名，不再硬编码中文

## 3. Risks and Notes

- MCP catalog 初始条目基于常见技术栈，实际 adoption 数据需从下游项目积累
- `harness feedback --import` 尚未实现（工具仓库侧导入），留待下个版本
- Level 2 MCP Server 通道仅完成接口设计，未实现
- 经验自动采集逻辑目前是模板和 hook 引导 Agent 手动记录，全自动采集需要 Agent 侧支持
