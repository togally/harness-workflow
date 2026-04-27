---
id: sug-39
title: "chg-01 派发钩子真实接通 record_subagent_usage（L-01 followup）"
status: pending
created_at: 2026-04-27
priority: medium
---

req-43（交付总结完善）/ chg-01（接通 record_subagent_usage 派发链路（吸收 sug-25））落地后 helper 实现正确（9/9 pytest 全过），harness-manager.md §3.6 Step 4 派发钩子升格为可观测留痕步骤（文字契约），但主 agent 在实际 session 中仍未执行 python helper 调用 — req-43 自身 usage-log.yaml 即缺失，反证 sug-25（record_subagent_usage 派发链路真实接通）精神未真正落地。建议起新 req 把派发钩子从「文字契约」升格为「runtime 强制调用」（如 Agent 工具返回 hook 中接入 record_subagent_usage 调用）。优先级 high。
