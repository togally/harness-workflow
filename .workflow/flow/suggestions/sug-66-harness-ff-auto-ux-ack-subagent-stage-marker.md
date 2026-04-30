---
id: sug-66
title: "harness ff --auto UX 误导：只 ack 决策点不派 subagent，但 stage marker 跳过"
status: pending
created_at: 2026-04-30
priority: medium
---

req-51 周期 Phase 1 → testing 实证：harness ff --auto 跳到 stage=testing 但未派任何 subagent 实际干活（只 ack 决策点 / stage marker 推进），主 agent 抓出后退回 analysis 重做。用户期待'快进 = 自动派 subagent 一路干完'与实际'快进 = 只标记 stage'严重错位。建议方向：(a) ff --auto 强制连续派 subagent；或 (b) ff --auto 文档明确不派活、stdout 提示 'stage marker 已推进，需手动 harness next 触发干活'。来源：req-51 / Phase 1 → testing 周转点。
