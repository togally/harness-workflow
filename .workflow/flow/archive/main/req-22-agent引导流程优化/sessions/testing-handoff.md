# Testing Handoff: req-22

## 触发原因
执行 executing 阶段已完成，需要独立 testing agent 验证 req-22 的交付物。

## 当前状态
- **需求**: req-22 - agent引导流程优化
- **阶段**: testing
- **当前变更**: 全部三个变更已执行完毕，包含三次 regression 修复和一轮 V3 测试后修复

## 已完成的步骤
- [x] chg-01: 创建技术总监角色，优化主 agent 引导入口
- [x] chg-02: 统一 stage 角色引导逻辑
- [x] chg-03: 优化关键节点与命令说明
- [x] Regression 修复 1：重构 technical-director.md 硬门禁、精简 context/index.md、更新 base-role.md
- [x] Regression 修复 2：极简化 WORKFLOW.md、重构 context/index.md 为"角色索引+加载流程"
- [x] Regression 修复 3：新建 role-loading-protocol.md、纯索引化 context/index.md、更新 WORKFLOW.md/technical-director.md/base-role.md
- [x] V3 测试后修复：删除 index.md 中的加载步骤说明、统一所有 stage 角色文件结构（删除本阶段任务/自验证 Checklist/对齐检查/独立返回值格式等）

## 需要验证的验收项

### chg-01 验收
1. `.workflow/context/roles/role-loading-protocol.md` 存在，定义所有角色通用加载步骤
2. `WORKFLOW.md` 引导语为：总结需求 → 去 `context/index.md` 找角色 → 按 `role-loading-protocol.md` 加载执行
3. `context/index.md` 是纯角色索引，无具体加载步骤说明，包含角色索引表格和 protocol 引用
4. `technical-director.md` SOP 引用 `role-loading-protocol.md`，包含硬门禁四
5. `base-role.md` 开头引用 `role-loading-protocol.md`

### chg-02 验收
6. 所有 stage 角色文件（requirement-review、planning、executing、testing、acceptance、regression、done、tools-manager）严格遵循 `ROLE-TEMPLATE.md` 的 11 个标准章节顺序
7. `ROLE-TEMPLATE.md` 要求 SOP 必须覆盖角色完整生命周期
8. `base-role.md` 中新增通用加载职责章节

### chg-03 验收
9. `stages.md` 命令-行为对应清晰
10. ff/regression/done 节点说明完整
11. `done.md` 中无 `changes_review` / `plan_review` 过时引用
12. `catalog/find-skills.md` 存在且定义了 skillhub 查询适配器
13. `keywords.yaml` 中注册了 `find-skills`
14. `tools-manager.md` 中不再硬编码 skillhub URL

### req-22 整体验收
15. requirement.md 中的 4 条验收标准均已覆盖

## 接管注意事项
1. 先读取 `.workflow/state/runtime.yaml` 确认状态
2. 读取 req-22 的 `requirement.md` 作为验收基准
3. 独立验证每个验收项，不要假设实现者已做对
4. 输出测试报告到 `.workflow/flow/requirements/req-22-agent引导流程优化/testing-report-v4.md`
5. 全部通过 → 报告完成；有任何未通过 → 记录缺陷并建议是否进入 regression
