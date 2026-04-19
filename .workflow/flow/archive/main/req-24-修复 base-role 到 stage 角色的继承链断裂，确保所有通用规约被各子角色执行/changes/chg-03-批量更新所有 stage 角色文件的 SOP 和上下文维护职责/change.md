# Change: 批量更新所有 stage 角色文件的 SOP 和上下文维护职责

## 目标

将所有 stage 角色文件（executing, testing, planning, acceptance, regression, requirement-review, done）的 SOP 和上下文维护职责与 `base-role.md` 和更新后的 `stage-role.md` 对齐。

## 范围

- 修改 `.workflow/context/roles/executing.md`
- 修改 `.workflow/context/roles/testing.md`
- 修改 `.workflow/context/roles/planning.md`
- 修改 `.workflow/context/roles/acceptance.md`
- 修改 `.workflow/context/roles/regression.md`
- 修改 `.workflow/context/roles/requirement-review.md`
- 修改 `.workflow/context/roles/done.md`

## 验收标准

- [x] 每个角色文件的 SOP 都包含：初始化（自我介绍+前置加载确认）、执行（工具优先查询+业务步骤+操作日志+60%上下文评估）、退出（经验沉淀检查+交接）
- [x] 每个角色的"上下文维护职责"中明确提到：任务执行过程中监控上下文，达到 60% 时必须评估 `/compact`/`/clear`
- [x] 每个角色的"可用工具"或 SOP 执行步骤中包含 toolsManager 查询
- [x] 每个角色在"退出条件"前增加"经验沉淀检查"步骤
- [x] 修改保持各角色的业务独特性，不模板化为完全一致的文字
