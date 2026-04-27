---
id: sug-48
title: "rename_requirement runtime 同步范围未来扩字段提醒（F-02 followup）"
status: pending
created_at: 2026-04-27
priority: low
---

req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） chg-02（rename CLI 同步范围扩展） plan.md §回滚 R-3 注明：runtime 未来若新增 `*_requirement_title` 类字段（如 pending_requirement_title / scheduled_requirement_title 等），需同步 rename_requirement 的 runtime 同步段（line 5462–5476 末尾）。当前仅同步 current_requirement_title / locked_requirement_title 两字段。建议在 workflow_helpers.py rename_requirement 末尾加注释提醒，或在 runtime schema 文档（如 .workflow/state/runtime.schema.md 若存在）显式列出 rename 同步白名单字段，避免未来扩字段时漏同步。
