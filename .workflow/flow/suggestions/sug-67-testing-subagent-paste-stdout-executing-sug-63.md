---
id: sug-67
title: "testing subagent 必须独立 paste 完整 stdout（不沿用 executing 错数字，与 sug-63 同型）"
status: pending
created_at: 2026-04-30
priority: medium
---

req-51 testing 阶段实证：testing subagent 报告全 suite '36 failed / 744 passed'，主 agent 独立实测 '51 failed / 729 passed'——疑似沿用 executing round-1 虚报的错数字未独立 pytest paste stdout。与 sug-63（lint 关键词清单必须由上级独立设计）同型。建议：在 testing.md 角色文件加'必须独立 paste 完整 stdout 才算汇报'红线条款，与 sug-63 形成 testing / executing 双向覆盖；reviewer 阶段 checklist 加同型 lint。来源：req-51 / testing 阶段 + test-report.md 末尾'主 agent 独立核查更正'段。
