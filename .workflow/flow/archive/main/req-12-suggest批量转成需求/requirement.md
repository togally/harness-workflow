# Requirement

## 1. Title

suggest 批量转成需求

## 2. Goal

当前 `harness suggest --apply <id>` 只能将单条 suggest 转化为需求。当 suggest 池中积累了多条建议时，用户需要多次执行 `--apply`，操作繁琐。

本需求的目标是：**新增一个批量转换命令，允许用户一次性将所有 pending 状态的 suggest 转化为正式需求**，提升 suggest 池的管理效率。

## 3. Scope

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

## 4. Acceptance Criteria

- [ ] `harness suggest --apply-all` 命令可用
- [ ] 命令能将所有 `status: pending` 的 suggest 批量转为正式需求
- [ ] 转化成功的 suggest 状态变为 `applied`
- [ ] 命令输出清晰的转换结果报告（成功/失败数量及对应 ID）
- [ ] 文档（README 或命令帮助）已更新

## 5. Split Rules

### chg-01 CLI 批量转换命令实现

在 `core.py` 和 `cli.py` 中实现 `apply_all_suggestions`：
- 扫描 `.workflow/flow/suggestions/` 下所有 suggest 文件
- 过滤 `status: pending`
- 逐条调用 `create_suggestion`
- 状态更新和结果汇总

### chg-02 文档更新与验证

- 更新 `README.md` 中 suggest 命令的说明
- 更新 `stages.md` 或命令帮助（如有必要）
- 在临时项目验证批量转换功能
- 重新打包安装并归档 req-12
