# chg-01 执行计划

## 依赖
无（可独立执行）

## 步骤

### Step 1：读取现有 context/index.md
确认当前加载顺序，找到补充位置。

### Step 2：更新 context/index.md 加载规则

**session-start 新增（最前）：**
- 读取 `tools/index.md` 了解工具系统结构

**Step 2 之后新增说明：**
- testing / acceptance / regression 阶段：在加载 `roles/{stage}.md` 后，还需加载 `evaluation/{stage}.md`

**新增步骤（项目与团队上下文）：**
- session-start：读取 `context/project/project-overview.md`
- before-task：读取 `context/team/development-standards.md`

### Step 3：补充 project-overview.md 内容
基于 `.workflow/` 结构和 `WORKFLOW.md`，填写六层架构对应表、演进背景、实践原则。

## 产物
- `.workflow/context/index.md`（已更新）
- `.workflow/context/project/project-overview.md`（已填充，本次已完成）
