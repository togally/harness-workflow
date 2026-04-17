# chg-01 Plan: 规范层更新

## 执行步骤

### Step 1: 更新 base-role.md
- 在"通用准则"或 SOP 章节中新增：
  > 每次角色开始执行实质性任务前，须向用户简要说明："我是 [角色名称]，接下来我将 [任务意图]。"
- 更新"角色标准工作流程约定"章节，将自我介绍纳入 SOP 初始化步骤

### Step 2: 完善 stages.md
- 确认 bugfix 快速流转图已包含完整的进入条件和退出条件
- 补充 `regression` 阶段在 bugfix 模式下的退出条件：diagnosis.md 完成且修复方案已写入 bugfix.md

### Step 3: 更新 review-checklist.md
- 新增 bugfix 目录结构检查项
- 新增 `harness bugfix` CLI 命令检查项（如已有 CLI 检查项则扩展）

### Step 4: 验证
- 运行 lint 脚本确认无结构问题
- 检查 `base-role.md` 和 `stages.md` 的一致性
