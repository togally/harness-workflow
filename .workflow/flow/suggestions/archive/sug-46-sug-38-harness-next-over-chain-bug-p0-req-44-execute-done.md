---
id: sug-46
title: "sug-38（harness next over-chain bug）升 P0：req-44 二次实证 --execute 仍连跳到 done"
status: applied
created_at: 2026-04-27
priority: high
---

本 req-44（apply-all artifacts/ 旧路径修复（bugfix-6 后遗症）） 周期再次实证 sug-38（harness next over-chain bug）：harness next --execute 触发后 stage 仍一次性自动跑完 executing → testing → acceptance → done（req-44.yaml stage_timestamps 中 executing/testing/acceptance/done 四段同在 02:00:28，差 < 7s）。主 agent 不得不手动 Edit runtime.yaml 滚回每个 stage 各派 subagent 才得以走完 stage gate。这是该 bug 的第二次跨 req 实证（继 sug-40（sug-38 meta-followup） 之后）。建议升级为 P0 紧急修复，根因排查 workflow_next while 循环 + verdict 路由 stage_policies 兜底，最迟下个 req 周期前修复。
