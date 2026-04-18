# Change: chg-01

## Title
打包与清理逻辑实现

## Goal
修改 `apply_all_suggestions`，支持将多条 pending suggest 打包成一个需求，并在成功后删除原 suggest 文件。

## Scope

**包含**：
- 修改 `core.py` 中的 `apply_all_suggestions` 函数
- 收集所有 pending suggest 的标题和 ID
- 生成默认打包标题（如 "批量建议合集（N条）"）
- 支持通过外部传入的 `--title` 覆盖默认标题
- 调用 `create_requirement` 生成一个 req
- 成功后删除所有被处理的 suggest 文件
- 更新输出报告格式

**不包含**：
- 修改单条 `--apply` 的行为
- 修改 `create_requirement` 的核心逻辑
- README 更新（由 chg-02 负责）

## Acceptance Criteria

- [ ] `--apply-all` 将所有 pending suggest 打包为**一个**需求
- [ ] 未指定 `--title` 时使用合理的默认标题
- [ ] 转化成功后，suggest 文件被**删除**（而非仅修改状态）
- [ ] 输出报告包含成功删除的 suggest 数量和生成的 req ID
- [ ] 无 pending suggest 时给出明确提示且不报错
