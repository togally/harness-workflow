# Change: chg-02

## Title

报告模板更新

## Goal

在 `done-report.md` 头部增加实现时长记录区块，并同步更新相关报告的头部格式规范。

## Scope

**包含**：
- 更新 `context/roles/done.md` 中的报告输出规范
- 在 `done-report.md` 头部增加"实现时长"固定字段
- 可选：同步更新 `testing-report.md`、`acceptance-report.md` 的头部格式
- 提供模板示例

**不包含**：
- 修改 done 阶段六层回顾检查的核心逻辑
- 修改非报告类的其他文档模板

## Acceptance Criteria

- [ ] `done.md` 中的报告规范包含时长记录要求
- [ ] 提供 `done-report.md` 头部模板示例，包含总时长和（可选）分阶段时长
- [ ] 模板格式统一、可读
