# suggest批量转成需求

> req-id: req-12 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

当前 `harness suggest --apply <id>` 只能将单条 suggest 转化为需求。当 suggest 池中积累了多条建议时，用户需要多次执行 `--apply`，操作繁琐。

本需求的目标是：**新增一个批量转换命令，允许用户一次性将所有 pending 状态的 suggest 转化为正式需求**，提升 suggest 池的管理效率。

## 交付范围

**包含**：
- 在 `harness suggest` 命令中新增 `--apply-all` 选项
- `--apply-all` 遍历 `.workflow/flow/suggestions/` 下所有 `status: pending` 的 suggest
- 对每条 pending suggest 自动调用 `create_requirement`，生成对应的 req-XX
- 将所有成功转化的 suggest 状态更新为 `applied`
- 输出批量转换的结果报告（成功列表、失败列表）
- 更新 CLI 和 skill 文档

**不包含**：
- 修改单条 `--apply` 的现有行为
- 自动执行转化后的需求（只负责创建需求，不自动进入 requirement_review 开始工作）
- 建议的优先级排序或筛选功能

## 验收标准

- [ ] `harness suggest --apply-all` 命令可用
- [ ] 命令能将所有 `status: pending` 的 suggest 批量转为正式需求
- [ ] 转化成功的 suggest 状态变为 `applied`
- [ ] 命令输出清晰的转换结果报告（成功/失败数量及对应 ID）
- [ ] 文档（README 或命令帮助）已更新

## 变更列表

- **chg-01** CLI 批量转换命令实现：在 `harness suggest` 中新增 `--apply-all` 选项，批量将所有 pending suggest 转为正式需求。
- **chg-02** 文档更新与验证：更新 README 中的 suggest 命令说明，验证批量转换功能，并归档 req-12。

## 关键设计决策

**chg-01**
- 复用现有的 `create_requirement` 函数，逐条创建需求
- 成功后通过字符串替换将 suggest 的 `status: pending` 更新为 `status: applied`
- 返回 0 当全部成功，返回 1 当有任何失败
**chg-02**
- 临时项目验证采用 `harness init` 创建干净项目，创建 2 条 suggest 后执行 `--apply-all`，成功转为 req-01 和 req-02
- 安装验证通过 `which harness` 确认 CLI 可用
