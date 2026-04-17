# Change: chg-01

## Title

工具层重构：基础角色、工具索引、评分与操作日志

## Goal

实现设计文档 `docs/superpowers/specs/2026-04-16-tool-layer-refactor-design.md` 中定义的全部内容。

## Scope

**包含**：
- `base-role.md` 及加载顺序修改
- `keywords.yaml`、`ratings.yaml`、`missing-log.yaml`
- `tool-search`、`tool-rate` CLI 命令
- `action-log.md` 写入逻辑
- `tools-manager.md` 角色文件及所有 stage 角色的 SOP 优化
- 对应测试

**不包含**：
- skill hub 的真实网络请求实现（当前仅预留接口）
- 重写现有 catalog 工具定义

## Acceptance Criteria

- [x] `base-role.md` 已创建并被 loader 引用
- [x] `tool-search` 能按关键词返回最匹配工具
- [x] `tool-rate` 能正确计算累计均分
- [x] 新增测试全部通过
- [x] `tools-manager.md` 已创建，含完整 SOP
- [x] 所有 stage 角色文件已增加标准工作流程（SOP）章节
