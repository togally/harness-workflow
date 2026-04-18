# Change: chg-01

## Title
regression 经验沉淀强制化

## Goal
在 regression 流程的任意结束分支中，自动确保存在对应的经验沉淀文件。

## Scope

**包含**：
- 修改 `core.py` 的 `regression_action`
- 新增 `_ensure_regression_experience(root, regression_id)`
- 在每个结束 regression 的分支前调用该函数
- `confirm` 分支现在也会结束 regression

**不包含**：
- 强制交互式输入经验内容
- 修改 CLI 参数

## Acceptance Criteria

- [ ] regression 结束时自动生成或检查经验文件
- [ ] 文件不存在时生成标准模板
- [ ] `confirm` 操作结束 regression 并留下经验记录
