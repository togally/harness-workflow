---
id: sug-40
title: "sug-38（harness next over-chain bug）修复优先级评估（meta-followup）"
status: pending
created_at: 2026-04-27
priority: medium
---

req-43（交付总结完善） dogfood 实证：harness next 在 verdict stage（testing / acceptance）链跳前未检查 subagent 工作是否实际完成，导致 executing 退出后一次性连跳到 done（testing / acceptance / done 的 entered_at 在同一秒内写入），acceptance subagent 不得不后补跑验证（见 acceptance/checklist.md L-03 留痕）+ done 阶段需手动滚回补跑测试与验收。本周期已是第二次实证此 bug 的影响面（req-43 自身），建议 sug-38（harness next over-chain bug）优先级评定为 high 并尽快起 bugfix 修复（给 verdict stage 加 subagent 工作完成 gate 检查，如 test-evidence.md / acceptance/checklist.md 存在 + 含 PASS/FAIL 结论）。
