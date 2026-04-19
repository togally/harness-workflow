# chg-02-suggest 转换约束文档（约束层修复）

## 目标
建立专门的约束文档，从制度层面禁止 `harness suggest --apply-all` 逐条拆分为独立需求，并将该约束注入到 planning 角色和审查检查清单中。

## 范围
- 新建 `.workflow/constraints/suggest-conversion.md`
- 修改 `.workflow/context/roles/planning.md`
- 修改 `.workflow/context/checklists/review-checklist.md`

## 变更内容
1. **新建约束文件** `.workflow/constraints/suggest-conversion.md`：
   - 明确规定 `harness suggest --apply-all` 必须将所有 pending suggest 打包为单一需求
   - 禁止逐条创建独立需求
   - 规定打包后的 `requirement.md` 必须包含所有 suggest 的标题和摘要列表
   - 声明违反本约束视为触发 regression
2. **注入 planning 角色**：在 `.workflow/context/roles/planning.md` 的"禁止的行为"或等效章节中引用 `suggest-conversion.md`，提醒架构师在拆分变更时注意 suggest 批量转换的打包要求
3. **更新审查检查清单**：在 `.workflow/context/checklists/review-checklist.md` 的 Constraints 层或 Flow 层增加对 suggest 转换约束的核对项

## 验收标准
- [ ] `.workflow/constraints/suggest-conversion.md` 存在且内容完整
- [ ] `planning.md` 中已引用该约束文件
- [ ] `review-checklist.md` 中已增加对应检查项
- [ ] 约束语义与 chg-01 的 CLI 强制打包行为一致，无冲突

## 依赖
- chg-01：建议先完成 chg-01 的 CLI 行为定义，再据此撰写约束文档，确保描述一致

## 阻塞
无。
