---
id: sug-32
title: "回 req-43（交付总结完善）端到端连跳自证"
status: pending
created_at: 2026-04-26
priority: medium
---

bugfix-5（同角色跨 stage 自动续跑硬门禁） §后续任务明确：bugfix-5 完成后主 agent 应回 req-43（交付总结完善）的 requirement_review → planning 流转点，跑一次 harness next 验证连跳逻辑——应一次性翻到 planning，不再出现'是否进 planning'决策点；若验证通过记一笔到 req-43 session-memory.md 作为 bugfix-5 修复点 2 的端到端自证；若验证失败立即起 bugfix-7 回归。本 sug 作为该后置任务的入池记录，避免主 agent 在 archive bugfix-5 后遗漏自证步骤。
