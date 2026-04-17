# Testing Handoff: req-22 (V5)

## 触发原因
第四次 regression 修复后的 executing 阶段已完成，需要独立 testing agent 验证 req-22 的新交付物（chg-04 和 chg-05）。

## 当前状态
- **需求**: req-22 - agent引导流程优化
- **阶段**: testing
- **当前变更**: chg-04（重构角色继承体系与 base-role 定位）+ chg-05（重构经验文件目录与加载规则）

## 已完成的步骤
- [x] chg-04 Step 1: 修改 role-loading-protocol.md（新增模型一致性声明、更新加载顺序为 base-role → stage-role → 具体角色）
- [x] chg-04 Step 2: 重构 base-role.md（重新定位为所有角色的通用规约，删除 stage 专属内容，新增经验沉淀规则和上下文维护规则含 60% 阈值）
- [x] chg-04 Step 3: 新建 stage-role.md（包含 Session Start、Stage 切换交接、经验文件加载规则、流转规则）
- [x] chg-04 Step 4: 更新 technical-director.md（subagent 加载流程改为三层继承）
- [x] chg-04 Step 5: 更新 context/index.md（新增 stage-role 条目）
- [x] chg-05 Step 1: 移动并重命名经验文件（stage/ → roles/，development.md → executing.md）
- [x] chg-05 Step 2: 更新 experience/index.md
- [x] chg-05 Step 3: stage-role.md 中经验加载规则已使用 roles/ 路径
- [x] chg-05 Step 4: 更新 done.md 中残留的经验引用
- [x] chg-05 Step 5~6: 验证 experience/stage/ 已删除、无残留引用

## 需要验证的验收项

### chg-04 验收
1. `role-loading-protocol.md` 中包含"所有角色必须使用与主 agent 相同模型"的明确声明
2. `role-loading-protocol.md` 中 stage 角色的加载顺序已更新为 `base-role.md → stage-role.md → {具体角色}.md`
3. `base-role.md` 的标题/引言不再限定为"stage 角色的抽象父类"，而是"所有角色的通用规约"
4. `base-role.md` 中无"流转规则（按需）"章节
5. `base-role.md` 中包含"经验沉淀规则"章节，定义沉淀时机、格式和路径
6. `base-role.md` 中包含"上下文维护规则"章节，明确 60% 阈值约束
7. `stage-role.md` 文件存在，包含 Session Start、Stage 切换交接、经验文件加载规则、流转规则 4 个章节
8. `technical-director.md` 中 subagent 加载流程描述与新的三层继承一致
9. `context/index.md` 中正确列出 `base-role.md` 和 `stage-role.md` 的继承关系

### chg-05 验收
10. `context/experience/stage/` 目录已不存在，文件已迁移到 `context/experience/roles/`
11. `context/experience/index.md` 正确列出 `roles/` 下的所有文件（acceptance.md、executing.md、planning.md、regression.md、requirement-review.md、testing.md）
12. `stage-role.md` 中的经验加载规则引用的是 `experience/roles/` 路径
13. 所有 stage 角色文件中无残留的 `experience/stage/` 路径引用
14. `technical-director.md` 和 `done.md` 中无残留的 `experience/stage/` 路径引用

### req-22 整体验收（回归修复验证）
15. 需求 requirement.md 中的 4 条验收标准仍被覆盖（各 stage 引导一致、命令对应明确、关键节点说明完整、全流程走查验证）

## 接管注意事项
1. 先读取 `.workflow/state/runtime.yaml` 确认状态
2. 读取 req-22 的 `requirement.md` 作为验收基准
3. 独立验证每个验收项，不要假设实现者已做对
4. 输出测试报告到 `.workflow/flow/requirements/req-22-agent引导流程优化/testing-report-v5.md`
5. 全部通过 → 报告完成；有任何未通过 → 记录缺陷并建议是否进入 regression
