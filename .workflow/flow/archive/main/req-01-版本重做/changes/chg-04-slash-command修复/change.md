# Change: chg-04 Slash Command 文件修复

## 关联需求
req-01 — 版本重做，AC-6

## 问题描述
regression 诊断（2026-04-13）确认以下 slash command 文件缺陷：
1. `.claude/commands/harness-exec.md` 映射不存在的 CLI 命令 `exec`（幽灵命令）
2. `harness-plan` 仅在 `.qoder`，`.claude` 和 `.codex` 缺失
3. `harness-feedback` 三端均无 slash command
4. 所有 slash command broken-state 提示引用旧版 `harness active "<version>"`

## 变更范围

**删除：**
- `.claude/commands/harness-exec.md`

**新增：**
- `.claude/commands/harness-plan.md`
- `.codex/skills/harness-plan/SKILL.md`（或等效文件）
- `.qoder/commands/harness-feedback.md`
- `.claude/commands/harness-feedback.md`
- `.codex/skills/harness-feedback/SKILL.md`（或等效文件）

**修改：**
- `.qoder/commands/*.md`、`.claude/commands/*.md`、`.codex/skills/harness-*/SKILL.md` 全部文件
  - 将 broken-state 提示从 `harness active "<version>"` 改为 `harness requirement "<title>"`

## 验收条件
- [ ] `harness exec` slash command 文件已删除
- [ ] 三端均有 `harness plan` slash command 且格式与其他命令一致
- [ ] 三端均有 `harness feedback` slash command 且格式与其他命令一致
- [ ] 全部 slash command 文件的 broken-state 提示使用新版措辞
