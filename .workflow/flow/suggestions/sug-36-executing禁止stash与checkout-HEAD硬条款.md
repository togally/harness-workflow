---
id: sug-36
title: executing 角色 SOP 加硬条款——禁止 `git stash pop` / `git checkout HEAD --`
status: pending
created_at: "2026-04-22"
priority: high
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）的 subagent 在开发过程中使用 `git stash pop` 恢复工作区，遇到冲突后用 `git checkout HEAD --` 兜底，**意外把 `.workflow/state/runtime.yaml` 回退到 req-31 done 状态**，导致 req-32 stage/current_requirement 记录丢失，主 agent 必须按 CLAUDE.md 硬门禁手工修复 runtime.yaml。

# 建议

在 `.workflow/context/roles/executing.md` 的"禁止的行为"或"完成前必须检查"章节增加硬条款：

- **禁止** `git stash pop` 后接 `git checkout HEAD --`（或任意覆盖式还原组合）
- **禁止** `git stash apply --force`
- **理由**：会污染 runtime.yaml / managed scaffold 文件，破坏 stage 一致性

若遇到工作树冲突，优先使用 `git stash show -p` 人工 review 后 `git checkout -p` 选择性恢复，或提请主 agent 介入。

# 验收

- `.workflow/context/roles/executing.md` 含新条款
- 同步 scaffold_v2 版本
- 不新增测试（属文档硬门禁）
