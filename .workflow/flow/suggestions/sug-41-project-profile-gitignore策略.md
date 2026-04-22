---
id: sug-41
title: `project-profile.md` 的 gitignore / commit 策略决策
status: pending
created_at: "2026-04-22"
priority: low
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-02（harness update 集成扫描器 + hash 漂移 + 用户自定义保护）落盘 `.workflow/context/project-profile.md`，但 `.gitignore` 规则 `/.workflow/` 让这份 profile 不入 git，导致：

- 协作者 clone 后必须跑 `harness update` 才有 profile
- profile 的 LLM 占位（项目用途 / 项目规范）内容不同步
- CTO 派发 task_context_index 引用的 profile 在新机上可能缺失

# 建议

三选一：

- **策略 A**：`.gitignore` 添加 `!.workflow/context/project-profile.md` 例外，profile 入 git，content_hash 保证稳定不产生无意义 diff
- **策略 B**：保持 gitignore 不变，改为 `harness install` 时自动 `harness update --scan-profile-only` 生成本地 profile
- **策略 C**：profile 迁移到制品仓 `artifacts/{branch}/project-profile.md`（已有 artifacts/ 挂载点）

评估三者的一致性 / 协作便利 / 动态性 tradeoff。

# 验收

- 策略决策记录在 `.workflow/constraints/` 或 `experience/` 新文档
- 相应修改 `.gitignore` / `harness install` / 路径常量
