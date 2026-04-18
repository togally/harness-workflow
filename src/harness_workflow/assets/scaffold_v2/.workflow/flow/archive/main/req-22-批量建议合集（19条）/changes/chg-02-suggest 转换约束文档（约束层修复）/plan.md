# chg-02-suggest 转换约束文档（约束层修复）执行计划

## 执行步骤

### Step 1：读取参考文件
- 读取 `.workflow/context/roles/planning.md`
- 读取 `.workflow/context/checklists/review-checklist.md`
- 读取 `.workflow/constraints/index.md`
- 读取 chg-01 的 change.md，确认 CLI 强制打包的最终语义

### Step 2：撰写约束文件
- 创建 `.workflow/constraints/suggest-conversion.md`
- 内容结构：
  1. 适用范围
  2. 强制打包规则
  3. 禁止行为
  4. requirement.md 内容要求
  5. 违规处理（视为 regression）

### Step 3：更新 planning.md
- 在 `planning.md` 的"禁止的行为"或"上下文维护职责"附近增加引用：
  - 提醒架构师：若需求源自 `harness suggest --apply-all`，必须确认 suggest 已按 `.workflow/constraints/suggest-conversion.md` 打包为单一需求

### Step 4：更新 review-checklist.md
- 在"六层检查框架 / Constraints 层"或"制品完整性检查专节"中增加检查项：
  - [ ] **suggest 转换打包检查（高）**：若本轮涉及 suggest 批量转换，是否遵守 `suggest-conversion.md` 的强制打包要求？有无逐条拆分为独立需求？

### Step 5：一致性校验
- 核对 chg-01 的 CLI 行为与约束文档描述是否一致
- 核对约束文件路径是否被 `constraints/index.md` 正确索引（如需要）

### Step 6：本地验证
- 运行 `harness validate`（如可用）检查文档格式
- 确认无 Markdown 语法错误

## 产物清单
- `.workflow/constraints/suggest-conversion.md`（新建）
- `.workflow/context/roles/planning.md`（修改）
- `.workflow/context/checklists/review-checklist.md`（修改）

## 预计消耗
- 文件读取：4-6 次
- 工具调用：约 8 次
- 风险：极低（纯文档变更）
