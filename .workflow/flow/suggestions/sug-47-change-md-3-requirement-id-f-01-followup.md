---
id: sug-47
title: "change.md §3 Requirement 字段裸 id（F-01 followup）"
status: pending
created_at: 2026-04-27
priority: low
---

req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） chg-01 / chg-02 的 change.md §3 Requirement 字段写为 `- `req-44`` 裸 id（模板结构字段，非叙述性引用），testing 与 acceptance 评估为 minor 不阻断。建议在 change.md template（CLI harness change 创建时落地的模板）的 §3 加 `- `{req-id}`（{req-title}）` 占位，或在 reviewer checklist 增加该字段的契约 7 豁免显式条款（明示模板结构字段属反向豁免外的可宽容项）。下一 req 起统一在 change.md §3 补短描述或在 template 加注释。
