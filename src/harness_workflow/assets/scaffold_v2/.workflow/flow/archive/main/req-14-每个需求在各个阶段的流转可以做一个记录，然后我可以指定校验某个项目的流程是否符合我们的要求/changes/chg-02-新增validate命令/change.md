# Change: chg-02

## Title
新增 validate 命令

## Goal
提供 `harness validate` 命令，自动检查当前激活需求的流程产物是否完整。

## Scope

**包含**：
- CLI 增加 `validate` 子命令
- 核心函数 `validate_requirement(root)` 检查当前 requirement 的所有 changes
- 检查每个 change 是否包含 `testing-report.md` 和 `acceptance-report.md`
- 输出缺失项列表

**不包含**：
- 自动修复缺失项
- 检查已归档需求

## Acceptance Criteria

- [ ] `harness validate` 能正确识别当前激活需求
- [ ] 缺失 testing-report 或 acceptance-report 的 change 会被列出
- [ ] 所有产物齐全时输出通过信息
