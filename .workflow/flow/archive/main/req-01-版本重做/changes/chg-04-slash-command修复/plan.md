# Plan: chg-04 Slash Command 文件修复

## 执行顺序

### Step 1 — 删除幽灵命令
- 删除 `.claude/commands/harness-exec.md`
- 验证：该文件不再存在

### Step 2 — 补充 harness-plan（cc 端）
- 创建 `.claude/commands/harness-plan.md`
- 内容格式参照 `.claude/commands/harness-next.md`（同平台同格式）
- 将 `argument-hint` 设为 `"<change>"`
- Focus 段落与 `.qoder/commands/harness-plan.md` 保持一致
- 验证：文件存在，frontmatter 格式正确

### Step 3 — 补充 harness-plan（codex 端）
- 创建目录 `.codex/skills/harness-plan/`
- 创建 `.codex/skills/harness-plan/SKILL.md`
- 内容格式参照 `.codex/skills/harness-next/SKILL.md`（同平台同格式）
- 验证：文件存在，frontmatter 含 `name: harness-plan` 和 `description`

### Step 4 — 补充 harness-feedback（三端）
- 创建 `.qoder/commands/harness-feedback.md`
- 创建 `.claude/commands/harness-feedback.md`
- 创建目录 `.codex/skills/harness-feedback/`
- 创建 `.codex/skills/harness-feedback/SKILL.md`
- 内容：
  - 映射 `harness feedback`
  - 描述：导出反馈事件摘要，支持 `--reset` 清空日志
  - 无特殊 Focus 段落（该命令无工作流语义）
- 验证：三端文件均存在，格式与同平台其他命令一致

### Step 5 — 批量更新 broken-state 提示（三端全部文件）
- 目标文件：
  - `.qoder/commands/harness-*.md`（共 ~19 个文件）
  - `.claude/commands/harness-*.md`（共 ~19 个文件）
  - `.codex/skills/harness-*/SKILL.md`（共 ~18 个文件）
- 替换内容：
  - 旧：`harness active "<version>"`
  - 新：`harness requirement "<title>"`
- 验证：全部目标文件中无旧措辞残留

## 产物清单
- 删除：`.claude/commands/harness-exec.md`
- 新增：`.claude/commands/harness-plan.md`
- 新增：`.codex/skills/harness-plan/SKILL.md`
- 新增：`.qoder/commands/harness-feedback.md`
- 新增：`.claude/commands/harness-feedback.md`
- 新增：`.codex/skills/harness-feedback/SKILL.md`
- 修改：三端全部 slash command 文件（broken-state 提示更新）

## 依赖
- 无前置变更依赖，可独立执行
- 建议先于 chg-05 执行（逻辑上更简单，先完成低风险部分）
