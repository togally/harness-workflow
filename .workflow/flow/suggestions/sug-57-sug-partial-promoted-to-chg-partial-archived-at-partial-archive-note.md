---
id: sug-57
title: "sug 模板补 partial_promoted_to_chg / partial_archived_at / partial_archive_note 字段语义化"
status: pending
created_at: 2026-04-28
priority: low
---

req-46 acceptance 阶段对 sug-53 引入 partial_promoted_to_chg + partial_archived_at + partial_archive_note 三个新字段（表达'部分主因 archived，部分主因 pending'语义），但契约 6 sug frontmatter 模板只列 5 必填字段（id/title/status/created_at/priority），未规范扩展字段。建议：补充 stage-role.md 契约 6 + sug 模板，把 partial_* 三字段列入'可选扩展字段'白名单 + 语义说明，并由 lint 校验字段名拼写。来源：req-46 acceptance 阶段 sug-53 引入字段。
