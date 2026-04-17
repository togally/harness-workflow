# chg-02 执行计划

## 依赖

- 前置变更：`chg-01`（技术总监角色创建完成，`context/index.md` 的加载顺序已更新）
- 依赖现有文件：`.workflow/context/roles/` 下所有角色文件

## 执行步骤

### Step 1: 定义统一模板
- [ ] 基于 `base-role.md` 和现有角色文件，提炼统一的 stage 角色模板
- [ ] 模板章节：角色定义 → SOP → 可用工具 → 允许/禁止行为 → 上下文维护职责 → 职责外问题处理 → 退出条件 → ff 模式说明 → 流转规则 → 完成前必须检查

### Step 2: 逐角色对齐
- [ ] `requirement-review.md`：按统一模板调整结构，补充缺失章节
- [ ] `planning.md`：按统一模板调整结构，补充缺失章节
- [ ] `executing.md`：按统一模板调整结构，补充缺失章节
- [ ] `testing.md`：按统一模板调整结构，补充缺失章节
- [ ] `acceptance.md`：按统一模板调整结构，补充缺失章节
- [ ] `regression.md`：按统一模板调整结构，补充缺失章节
- [ ] `done.md`：按统一模板调整结构，补充缺失章节
- [ ] `tools-manager.md`：按统一模板调整结构，补充缺失章节

### Step 3: 检查一致性
- [ ] 读取 `base-role.md`，确认与统一模板无冲突
- [ ] 检查各角色的"流转规则"章节，确认与 `stages.md` 一致
- [ ] 检查各角色的"退出条件"，确认可验证、无歧义
- [ ] 补充 session start 和 stage 切换的上下文交接说明

### Step 4: 验证
- [ ] 快速浏览所有角色文件，确认结构统一
- [ ] 记录任何无法在当前变更中解决的冲突（留给 chg-03 或后续处理）

## 产物

- 更新后的 `.workflow/context/roles/` 下所有角色文件
- （可选）`.workflow/context/roles/ROLE-TEMPLATE.md` 作为后续新增角色的参考模板
