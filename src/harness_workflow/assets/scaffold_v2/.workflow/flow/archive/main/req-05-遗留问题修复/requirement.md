# Requirement

## 1. Title

遗留问题修复：resolve 前缀匹配 + 结构化验证阶段 + 开发文档

## 2. Goal

修复 req-05「功能扩展」完成后遗留的问题，并对工作流流程质量做出结构性增强：

1. **resolve 前缀匹配 bug**（已热修复，本需求补全）：`resolve_change_reference` 与 `resolve_requirement_reference` 存在同样的缺少前缀匹配问题
2. **WORKFLOW_SEQUENCE 增加 testing/acceptance 结构化自验证阶段**：
   - 语义：testing = executing agent 逐项检查所有 AC 是否满足；acceptance = 对 change.md 和 requirement.md 的结构化对齐检查
   - 不是外部 QA，是流程强制的内部检查节点，防止 executing 阶段草率通过
3. **开发体验文档**：源码变更后需手动 `pipx inject --force`，缺文档说明
4. **archive 行为说明**：`harness archive req-id` 仅处理 done 状态需求，行为正确但缺说明

## 3. Scope

**包含**：
- `resolve_change_reference` 增加前缀匹配（与 `resolve_requirement_reference` 一致）
- `WORKFLOW_SEQUENCE` 在 `executing` 之后增加 `testing`、`acceptance` 两个阶段
- `workflow_next()` 逻辑更新（`executing → testing → acceptance → done`）
- `context/roles/testing.md`、`context/roles/acceptance.md` 已有角色文件内容确认/完善（作为结构化自验证 checklist）
- `context/index.md` 路由表更新（testing/acceptance 阶段加载对应角色和 evaluation 文件）
- 开发文档增加「本地开发验证」步骤（`pipx inject --force`）
- README 补充 `harness archive` 仅限 done 状态说明

**不包含**：
- 新增外部 QA 机制
- 修改 testing/acceptance 以外的其他 WORKFLOW_SEQUENCE 阶段

## 4. Acceptance Criteria

- [ ] `harness archive req-xx`（短 ID）能正确解析含标题的目录名
- [ ] `harness change --requirement req-xx`（短 ID 引用）同样正确解析
- [ ] `harness next` 从 executing 推进到 testing，再到 acceptance，再到 done（三步）
- [ ] `context/roles/testing.md` 包含明确的自验证 checklist（每条 AC 逐项检查）
- [ ] `context/roles/acceptance.md` 包含 requirement.md 对齐检查 checklist
- [ ] 开发文档包含 `pipx inject harness-workflow . --force` 说明
- [ ] README 中说明 `harness archive` 仅处理 done 状态需求

## 5. Split Rules

待 requirement_review 确认后拆分变更。
