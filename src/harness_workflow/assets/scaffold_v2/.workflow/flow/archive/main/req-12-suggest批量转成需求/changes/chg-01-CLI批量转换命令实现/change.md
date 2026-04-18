# Change: chg-01

## Title
CLI 批量转换命令实现

## Goal
在 `harness suggest` 中新增 `--apply-all` 选项，批量将所有 pending suggest 转为正式需求。

## Scope

**包含**：
- 在 `cli.py` 中新增 `--apply-all` 参数
- 在 `core.py` 中实现 `apply_all_suggestions(root)` 函数
- 遍历 `.workflow/flow/suggestions/` 下 `status: pending` 的 suggest
- 逐条调用 `create_requirement`
- 输出转换结果报告

**不包含**：
- 修改单条 `--apply` 的现有行为
- 自动开始执行转化后的需求

## Acceptance Criteria

- [ ] `harness suggest --apply-all` 命令可用
- [ ] 所有 pending suggest 被批量转为 req
- [ ] 转化成功的 suggest 状态变为 `applied`
- [ ] 输出清晰的转换结果报告
