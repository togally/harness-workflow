---
id: sug-59
title: "done_efficiency_aggregate 路径漂移：req-46 实际数据在 state/sessions/ 但 helper 找 flow/requirements/"
status: pending
created_at: 2026-04-28
priority: high
---

done 六层回顾时发现：done_efficiency_aggregate(root, 'req-46', task_type='req') 返回全部 ⚠️ 无数据，但实际 .workflow/state/sessions/req-46/usage-log.yaml 9 条 entries 完整存在。根因：helper 内部对 task_type='req' 走 .workflow/flow/requirements/{req-id}-{slug}/usage-log.yaml 路径（req-41+ 新位），而 record_subagent_usage 写入路径仍是 .workflow/state/sessions/{req-id}/usage-log.yaml（旧位）— 写读路径不一致。建议：①修 record_subagent_usage 写入路径对齐 helper 读路径；或 ②修 helper 读路径回退 state/sessions/。这是 sug-39 钩子接通前的另一根因。来源：req-46 done 阶段实证。
