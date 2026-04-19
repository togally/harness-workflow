# chg-02 session memory

## 变更目标
建立正式的约束文档，从制度层面确保 `harness suggest --apply-all` 永远不会再被错误拆分成多个独立需求。

## 修改步骤

1. 新建 `.workflow/constraints/suggest-conversion.md`
   - 定义约束标题、适用范围、核心规则（4条）、例外情况（无例外）、检查点。

2. 修改 `.workflow/context/roles/planning.md`
   - 在"完成前必须检查"列表末尾追加第5条：
     > 若本次变更涉及 suggest 批量转换，必须确认已阅读 `.workflow/constraints/suggest-conversion.md`，并确保所有 suggest 被打包为单一需求。

3. 修改 `.workflow/context/checklists/review-checklist.md`
   - 在"第六层：Constraints（约束层）"末尾增加高优先级检查项：
     > - [ ] `[高]` suggest 批量转换操作是否遵守 `.workflow/constraints/suggest-conversion.md` 的打包要求

## 修改的文件路径
- `/Users/jiazhiwei/claudeProject/harness-workflow/.workflow/constraints/suggest-conversion.md`（新建）
- `/Users/jiazhiwei/claudeProject/harness-workflow/.workflow/context/roles/planning.md`（修改）
- `/Users/jiazhiwei/claudeProject/harness-workflow/.workflow/context/checklists/review-checklist.md`（修改）

## 关键内容摘要
- 核心规则：`--apply-all` 必须将所有 pending suggest 打包为单一需求，禁止逐条创建独立需求；打包后的 `requirement.md` 必须包含所有 suggest 的标题和摘要列表；违反约束视为 regression。
- 无例外：即使 suggest 数量再多、主题差异再大，也必须打包为一个需求，在需求内部通过变更拆分来处理。
- 检查点：执行 `suggest --apply-all` 前，agent 必须确认自己正在使用 `--pack-title` 或接受默认打包行为。
