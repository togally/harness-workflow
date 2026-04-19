# chg-02-审查员角色定义 执行计划

## 执行步骤

1. **调研现有角色模板**
   - 读取 `.workflow/context/roles/planning.md`、`.workflow/context/roles/executing.md`、`.workflow/context/roles/done.md`
   - 提取角色文件的通用结构（角色定义、本阶段任务、允许行为、禁止行为、上下文维护职责、退出条件等）

2. **定义审查员核心行为**
   - 确定审查员在 requirement_review、planning、testing、acceptance、done 各阶段的介入方式
   - 确定审查员与主 agent、subagent 的交互关系（审查员是否由 subagent 扮演、主 agent 如何调度）
   - 确定审查结论的流转规则（pass → 进入下一阶段；reject → 退回并说明原因；needs_rework → 记录问题清单）

3. **编写审查员角色文件**
   - 新建 `.workflow/context/roles/reviewer.md`
   - 按通用结构填充内容
   - 在“本阶段任务”中明确引用 `.workflow/context/checklists/review-checklist.md`
   - 添加“审查结论模板”小节，包含 pass / reject / needs_rework 的标准输出格式

4. **内部验证**
   - 对照 change.md 验收条件逐条核对
   - 确认角色边界描述清晰，不会与 planning、executing、testing 角色冲突

## 产物清单
- `.workflow/context/roles/reviewer.md`

## 依赖关系
- 无前置依赖
- 被 chg-03 依赖（chg-03 需在现有角色文件中提示审查员角色的存在和清单更新检查）

## 执行顺序
第 1 顺位（可与 chg-01 并行执行）
