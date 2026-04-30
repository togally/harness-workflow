---
id: sug-63
title: "硬门禁九扩展：lint 关键词清单必须由上级独立设计（不允许 subagent 自报）"
status: pending
created_at: 2026-04-29
priority: high
---

bugfix-11（PetMallPlatform-artifacts误放机器型流程文档）round-2 regression 诊断 H-C 主导根因：round-1 executing subagent 自报 'lint 0 命中'，但其 grep 关键词清单本身漏掉 _use_flow_layout（仅含 _use_flat_layout/FLAT_LAYOUT_FROM_REQ_ID/FLOW_LAYOUT_FROM_REQ_ID），上级如果照抄 subagent 提供的 grep 关键词跑核查 = 和 subagent 同步盲。base-role.md 硬门禁九目前覆盖'代码改动类必跑 grep/pytest'，但未约束'lint 关键词清单的产出方'。建议扩条款：subagent 报告 lint 通过时，上级核查的 grep 关键词清单必须由上级（或用户红线 required-inputs.md）独立设计，禁止照抄 subagent 自报关键词；可加 lint 关键词清单 hash 留痕到 session-memory 防偷换。来源：bugfix-11 regression round-2 diagnosis-round2.md §7 #2。
