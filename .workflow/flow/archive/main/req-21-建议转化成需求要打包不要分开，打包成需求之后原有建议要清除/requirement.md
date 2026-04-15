# Requirement

## 1. Title

suggest 批量转需求支持打包与自动清理

## 2. Background

当前 `harness suggest --apply-all` 的行为是：每条 pending suggest 都单独调用 `create_requirement`，生成一个独立的 req-XX。当 suggest 池中有大量相关建议时，会产生过多零散需求，不利于后续管理和跟踪。

此外，转化成功后的 suggest 文件仅被修改 `status: applied`，文件本身仍然保留在 `.workflow/flow/suggestions/` 目录中，长期积累会造成 suggest 池膨胀、难以辨识真正 pending 的建议。

## 3. Goal

优化 `harness suggest --apply-all` 的批量转化行为：
1. **支持打包模式**：允许用户将多条 suggest 合并（打包）成**一个**正式需求，而不是每条 suggest 都单独生成一个需求。
2. **自动清理**：批量转化成功后，**删除**原 suggest 文件，而不是仅修改状态。

## 4. Scope

**包含**：
- 在 `harness suggest --apply-all` 中新增打包逻辑
- 支持自动生成一个汇总型需求标题（如 "批量建议合集：xxx, yyy..."），或允许用户在执行时指定打包后的需求标题
- 转化成功后删除已处理的 suggest 文件
- 输出报告包含：被删除的 suggest 列表、生成的 req 信息
- 更新 CLI 帮助文本和 README 文档
- 同步更新 `scaffold_v2`

**不包含**：
- 修改单条 `harness suggest --apply <id>` 的现有行为（仍保持单条转单需求）
- suggest 的优先级排序、分类筛选功能
- 自动进入 requirement_review 或开始执行转化后的需求

## 5. Acceptance Criteria

- [ ] `harness suggest --apply-all` 支持将所有 pending suggest 打包为**一个**需求
- [ ] 打包后的需求标题可由用户指定（如 `--apply-all --title "优化测试与经验沉淀"`），若未指定则使用自动生成的默认标题
- [ ] 转化成功后，所有被处理的 suggest 文件从 `.workflow/flow/suggestions/` 中**删除**
- [ ] 命令输出清晰的转换结果报告（成功删除的 suggest 数量及对应 ID、生成的 req ID）
- [ ] 当 suggest 池为空或无 pending suggest 时，命令给出明确提示且不报错
- [ ] CLI 帮助和 README 文档已更新

## 6. Split Rules

### chg-01 打包与清理逻辑实现
- 修改 `core.py` 中的 `apply_all_suggestions` 函数
- 实现打包模式：收集所有 pending suggest 的标题，合并生成一个 req
- 支持 `--title` 参数覆盖默认标题
- 转化成功后删除 suggest 文件而非修改状态
- 更新输出报告格式

### chg-02 文档与验证
- 更新 `cli.py` 中 `--apply-all` 的参数说明（新增 `--title`）
- 更新 `README.md` 和 `scaffold_v2/README.md`
- 在临时项目验证打包转换和文件清理行为
- 重新安装包并产出测试/验收报告
