---
id: sug-62
title: "_next_req_id 跨 branch 不扫归档导致下游切新 branch 起步重号风险"
status: pending
created_at: 2026-04-29
priority: medium
---

bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）regression round-1 诊断捕获：CLI 内部 _next_req_id 仅扫描当前 git branch 视角下的 .workflow/state/requirements/ 与 .workflow/flow/archive/{branch}/，下游用户仓切到新 branch（如 PetMallPlatform 从 member 切 v1.0.0）后 max_num 归零，再次返回 req-01；与原 branch 的 req-01 在 git log/状态层重号，归档/批处理时混淆。建议：_next_req_id 扫描扩展到全 branch 归档目录（或至少 main + 当前 branch）取 max + 1；与 bugfix-11 root cause 同源（CLI 假设 req-id 单调递增于自身仓 timeline）但维度不同（重号 vs 路径），独立修复。来源：bugfix-11 regression round-1 diagnosis.md §待处理捕获问题 + round-2 §7 #1 同根因连带。
