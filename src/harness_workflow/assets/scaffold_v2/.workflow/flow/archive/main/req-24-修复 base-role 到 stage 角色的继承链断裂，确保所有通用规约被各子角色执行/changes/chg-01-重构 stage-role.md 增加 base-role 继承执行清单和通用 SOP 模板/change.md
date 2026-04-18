# Change: 重构 stage-role.md，增加 base-role 继承执行清单和通用 SOP 模板

## 目标

修复 `stage-role.md` 作为中间层未能有效翻译 `base-role.md` 通用规约的问题，使其成为所有 stage 角色必须遵循的可执行父类。

## 范围

- 修改 `.workflow/context/roles/stage-role.md`
- 不修改 `base-role.md` 本身

## 验收标准

- [x] `stage-role.md` 中新增"继承自 base-role 的执行清单"章节，将 base-role 的 5 条核心要求映射为可检查的子类行为
- [x] `stage-role.md` 中新增"通用 SOP 模板"，明确所有 stage 角色的 SOP 必须包含：初始化（自我介绍+前置加载）、执行（工具优先+操作日志+上下文监控）、退出（经验沉淀+交接）三个部分
- [x] 各具体 stage 角色的原有业务逻辑（Step 1~N）被明确纳入"执行"部分，不得与通用步骤冲突
