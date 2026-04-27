---
id: sug-42
title: "tokens 真实计算方案 + 实施（含与 sug-39 接通后的下游消费）"
status: pending
created_at: 2026-04-27
priority: high
---

现状：交付总结 §效率与成本 token 列在所有归档 req 都是 ⚠️ 无数据；根因 chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））派发钩子是文字契约（sug-39 已登记）。本 sug 在 sug-39 之上加'下游消费方案'：1. record_subagent_usage entry 必含 input_tokens / output_tokens / cache_read_input_tokens / cache_creation_input_tokens / total_tokens / tool_uses 6 字段（已 schema 化，等接通）；2. done_efficiency_aggregate 单表渲染逻辑保留（chg-03 已落），新增 fallback：usage-log 无 entries → 不输出 token 列，输出说明性 footer；3. 可选：派发钩子失败时主 agent 写 stub entry（最小留痕：role/model/timestamp，token 字段 null），保证 entries 数 ≥ 派发次数 - 容差不退化。
