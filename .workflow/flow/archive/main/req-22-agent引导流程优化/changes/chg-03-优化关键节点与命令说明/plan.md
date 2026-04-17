# chg-03 执行计划

## 依赖

- 前置变更：`chg-01`（主入口已更新）、`chg-02`（stage 角色已统一）
- 依赖现有文件：`.workflow/flow/stages.md`、`.workflow/constraints/boundaries.md`、`.workflow/constraints/recovery.md`

## 执行步骤

### Step 1: 优化 stages.md
- [ ] 梳理命令与 stage 的对应关系表格，确保每个命令的作用和适用 stage 清晰
- [ ] 检查 ff 模式章节，补充或明确：启动条件、各 stage 自动完成判定、session-memory 规范、暂停与退出机制
- [ ] 检查 regression 流转路径，确保图示和文字说明一致
- [ ] 检查 done 阶段的进入条件和归档规则

### Step 2: 检查约束文件
- [ ] 读取 `constraints/boundaries.md`，确认 ff 模式下 AI 自主决策边界与 `technical-director.md` / 各 stage 角色一致
- [ ] 读取 `constraints/recovery.md`，确认失败恢复路径与 `regression.md` 一致
- [ ] 如有冲突或遗漏，同步更新

### Step 3: 检查 done.md 清单
- [ ] 读取 `context/roles/done.md`
- [ ] 确认六层回顾检查清单完整
- [ ] 确认工具层专项检查和经验沉淀验证步骤无遗漏

### Step 4: 全流程走查验证
- [ ] 模拟一条需求从 `requirement_review` → `planning` → `executing` → `testing` → `acceptance` → `done` 的流转路径
- [ ] 在每个 stage 切换点检查：
  - 技术总监角色是否能正确加载并派发 subagent
  - stage 角色的 SOP 和退出条件是否清晰
  - `harness next` / `harness ff` / `harness regression` 的触发条件是否明确
- [ ] 输出走查报告，记录发现的问题和修复状态

### Step 5: 收尾
- [ ] 修复走查中发现的问题（若为小范围调整）
- [ ] 若问题超出本变更范围，记录到走查报告中作为后续跟进项
- [ ] 更新 req-22 的 `session-memory.md`

## 产物

- 更新后的 `.workflow/flow/stages.md`
- 更新后的 `constraints/boundaries.md`（如有修改）
- 更新后的 `constraints/recovery.md`（如有修改）
- 走查报告（可放在 `.workflow/flow/requirements/req-22-agent引导流程优化/session-memory.md` 或独立文件中）
