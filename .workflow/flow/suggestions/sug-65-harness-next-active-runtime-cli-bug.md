---
id: sug-65
title: "harness next 多 active 推进异常清空 runtime（CLI bug）"
status: pending
created_at: 2026-04-30
priority: high
---

req-51 acceptance 阶段实证：harness next 在 testing → acceptance 推进时异常清空 runtime（active_requirements / current_requirement 全空），但 req-51.yaml + bugfix-11.yaml 状态保留。主 agent 手动恢复 runtime.yaml 后才能继续 acceptance。多 active_requirements（[bugfix-11, req-51]）场景下推进的疑似 CLI bug，与主 req 主线无关，独立修复。来源：req-51 / acceptance 阶段 + action-log.md 2026-04-29T16:52:05Z 条目。
