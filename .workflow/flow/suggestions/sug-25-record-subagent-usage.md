---
id: sug-25
title: "record_subagent_usage 派发链路真实接通"
status: applied
created_at: 2026-04-25
applied_at: 2026-04-26
priority: high
applied_by: "req-43（交付总结完善）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））"
---

主 agent 每次 Agent 工具返回后必调 record_subagent_usage（chg-08 文字契约已立但运行时未接入）；done 六层回顾 State 层自检发现 usage-log entries < 派发次数即阻断 done 推进
