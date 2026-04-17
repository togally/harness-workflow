# chg-02: 统一 stage 角色引导逻辑

## 目标

梳理并统一 Harness Workflow 各 stage 角色文件的上下文加载、SOP、流转规则，消除角色之间的冲突和遗漏，使 agent 在各 stage 的引导路径连贯一致。

## 范围

### 包含

- 检查并统一以下角色文件的结构和引导逻辑：
  - `.workflow/context/roles/requirement-review.md`
  - `.workflow/context/roles/planning.md`
  - `.workflow/context/roles/executing.md`
  - `.workflow/context/roles/testing.md`
  - `.workflow/context/roles/acceptance.md`
  - `.workflow/context/roles/regression.md`
  - `.workflow/context/roles/done.md`
  - `.workflow/context/roles/tools-manager.md`
- 统一各角色入口格式：角色定义 → SOP → 可用工具 → 允许/禁止行为 → 上下文维护职责 → 职责外问题处理 → 退出条件 → ff 模式说明 → 流转规则 → 完成前必须检查
- 补充关键节点缺失说明（如 session start 时如何加载、stage 切换时如何交接上下文）
- 检查 `base-role.md` 与各 stage 角色的一致性

### 不包含

- 修改 `WORKFLOW.md` 和 `context/index.md`（由 chg-01 负责）
- 修改 `.workflow/flow/stages.md`（由 chg-03 负责）
- 引入新的 stage 或角色

## 验收标准

- [ ] 所有 stage 角色文件采用统一的章节结构
- [ ] 各角色的 SOP 与 `stages.md` 的流转规则一致
- [ ] 各角色的退出条件明确且可验证
- [ ] `base-role.md` 与各 stage 角色无冲突
- [ ] 关键引导节点（session start、stage 切换）的说明完整
