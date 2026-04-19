# Change: chg-01

## Title

suggest 数据模型与存储设计

## Goal

确定 suggest 的存储路径、文件命名规范和内容格式。

## Scope

**包含**：
- 存储路径：`.workflow/flow/suggestions/`
- 文件命名：`sug-{两位数字}-{slug}.md`
- 内容格式：Markdown 头部包含 id、created_at、content、status
- ID 生成规则：从现有 suggestion 中找最大序号 +1

**不包含**：
- CLI 命令实现
- UI 界面

## Acceptance Criteria

- [ ] 文档化 suggest 的存储规范
- [ ] 提供示例文件格式
