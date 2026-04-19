# chg-03-Harness Skill 层提示 — session memory

## 变更摘要
在 Harness Skill 文档中为 `harness suggest --apply-all` 增加强制打包的显式提示，确保 Claude Code agent 在执行批量 suggest 转换前主动检查约束。

## 修改文件
1. `.claude/skills/harness/SKILL.md`
2. `.qoder/skills/harness/SKILL.md`
3. `.codex/skills/harness/SKILL.md`

## 修改内容
在 Command Model 中新增第 8 条命令 `harness suggest`，并在其下增加子章节：

### `harness suggest --apply-all` 强制打包要求

执行 `harness suggest --apply-all` 前，必须：
1. 检查 `.workflow/constraints/suggest-conversion.md` 是否存在并阅读其约束
2. 确保使用 `--pack-title` 或将所有 pending suggest 打包为**单一需求**
3. 禁止手写脚本逐条创建独立需求
4. 打包后的 `requirement.md` 必须包含所有 suggest 的标题和摘要列表

## 关键决策
- 原 `.claude/skills/harness/SKILL.md` 和 `.qoder/skills/harness/SKILL.md`、`.codex/skills/harness/SKILL.md` 内容完全一致，但均未包含 `harness suggest` 命令说明。为保持多平台 skill 一致性，三处同步修改。
- 插入位置选在 Command Model 的 `harness regression` 之后、`## Routing Rules` 之前，符合计划要求的最小侵入方式。

## 遇到的问题
无。

## 下一步
无。本变更已完成，可进入验收或下一变更。
