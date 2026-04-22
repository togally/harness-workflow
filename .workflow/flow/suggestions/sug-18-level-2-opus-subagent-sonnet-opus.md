---
id: sug-18
title: "Level-2 opus subagent 派发契约硬门禁（防 Sonnet 内联跑 opus 角色）"
status: pending
created_at: 2026-04-22
priority: medium
---

req-32 chg-03 端到端自证时，E-4 默认 Level-1 自跑导致 executing (Sonnet) 内联执行 project-reporter (opus) 的 10 节 SOP，偏离 role-model-map.yaml 契约。建议 harness-manager.md Step 2.5 追加硬门禁：派发 opus 角色 subagent 时必须显式调 Agent 工具传 model: opus，不得由 Sonnet subagent 内联执行 opus 角色任务。
