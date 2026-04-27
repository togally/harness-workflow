---
id: sug-50
title: "chg-01 gate gap：第一格修了但 while 循环内 gate 缺失，多格连跳还会越过 acceptance→done"
status: pending
created_at: 2026-04-27
priority: high
---

req-45（harness next over-chain bug 修复（紧急）） chg-01（verdict stage work-done gate + workflow_next 集成） 2nd executing 修 BUG-01（gate 插桩位置错）时把 gate 从 while 循环内挪到第一格 _write_stage_transition 前，结果**第一格放行后 while 循环内的多格连跳没保护**。req-45 testing 完成后跑 harness next dogfood 实证：testing→acceptance 第一格正确放行（test-report.md 存在含 §结论），但接下来 while 循环内 acceptance→done 第二格连跳照样跳过去（acceptance/checklist.md 不存在但 gate 不查）。修复方向：gate **同时**保留在第一格转换前 + while 循环内每次连跳前；或抽象成 helper  在两个位置共用。优先级 high，下一个 req 紧急做。
