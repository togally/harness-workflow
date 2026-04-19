# Plan: chg-03

## Steps

1. 参考现有 `harness-requirement.md` 的格式，创建 `harness-suggest.md`
2. 使用 `harness update` 或手动复制，确保四个平台都有对应文件
3. 检查 `.qoder/rules/harness-workflow.md` 是否需要更新命令列表
4. 验证文件存在性

## Artifacts

- `.claude/commands/harness-suggest.md`
- `.codex/skills/harness-suggest/SKILL.md`
- `.qoder/commands/harness-suggest.md`
- `.kimi/skills/harness-suggest/SKILL.md`

## Dependencies

- 依赖 chg-02 的 CLI 命令已稳定
