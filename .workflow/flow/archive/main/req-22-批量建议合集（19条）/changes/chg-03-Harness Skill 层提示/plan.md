# chg-03-Harness Skill 层提示执行计划

## 执行步骤

### Step 1：读取 SKILL.md
- 读取 `.claude/skills/harness/SKILL.md`
- 定位 `harness suggest` 相关描述位置（Command Model 或 Routing Rules 附近）

### Step 2：确定插入位置和内容
- 在 Command Model 的 `harness suggest` 条目下，或 Routing Rules 中增加显式提示
- 提示内容：
  - 执行 `harness suggest --apply-all` 前，检查 suggest 池约束
  - 优先使用 `--pack-title` 将所有 pending suggest 打包为单一需求
  - 禁止逐条拆分为独立需求

### Step 3：修改 SKILL.md
- 以最小侵入方式插入提示段落
- 保持现有 Markdown 结构和格式一致

### Step 4：一致性校验
- 核对 Skill 提示与 chg-01 CLI 行为、chg-02 约束文档是否一致
- 确认无语法错误或链接断裂

### Step 5：本地验证
- 预览修改后的 SKILL.md，确认渲染正常

## 产物清单
- `.claude/skills/harness/SKILL.md`（修改）

## 预计消耗
- 文件读取：2-3 次
- 工具调用：约 5 次
- 风险：极低（单文件文档补充）
