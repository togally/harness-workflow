---
id: sug-53
title: "req-45 done 六层 State 层校验：usage-log.yaml 仍缺（sug-39 派发钩子未接通的二次实证）— 升 sug-39 优先级 high"
status: pending
created_at: 2026-04-27
priority: medium
---

req-45（harness next over-chain bug 修复（紧急）） done 阶段执行 State 层 grep 校验：.workflow/state/sessions/req-45-harness-next-over-chain-bug-修复-紧急/usage-log.yaml 不存在 → entries 数 = 0；req 周期已派发 ≥ 6 个 subagent（analyst×2 / executing×2 / testing×2 / acceptance / 本 done）→ 容差判 usage 采集严重不完整。根因 = sug-39（chg-01 派发钩子真实接通 record_subagent_usage）至今未做（req-43 chg-01 helper 加了 task_type 参数但派发链路 record_subagent_usage 没被主 agent 真正调用）。本 sug 作 sug-39 的二次实证 + 升 priority 凭证：req-43 / req-44 / req-45 三连 req 都缺 usage-log，交付总结 §效率与成本表全部 ⚠️ 无数据，token / duration 失真。建议下一 req 周期把 sug-39 升 P0 直接处理。
