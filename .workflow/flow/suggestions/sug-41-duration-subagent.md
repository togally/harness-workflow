---
id: sug-41
title: "时间统计口径修正：duration = subagent 工作时间，不含阶段间用户等待"
status: pending
created_at: 2026-04-27
priority: high
---

现状：stage_timestamps[N+1].entered_at - stage_timestamps[N].entered_at = stage N 'duration'，**含人类等待时间**（用户思考/审阅/睡觉）。req-43（交付总结完善）实证 38.7h 总耗时大头是用户等待。新口径：duration = subagent dispatch 开始 → subagent return 实际工作秒数（取 record_subagent_usage entry 的 duration_ms 累加）；流转点之间的人类等待不算入。需要：1. record_subagent_usage entry 加 dispatch_start_ts / return_ts 字段（chg-01 接通后落地）；2. done.md §效率与成本段 duration_s 列从 stage_timestamps diff 改为 sum(usage entries.duration_ms)/1000；3. 兼容老 entries（无字段时 fallback 到 stage_timestamps diff 并标 ⚠️ 旧口径）。
