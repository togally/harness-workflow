---
id: sug-38
title: "harness next 在 verdict stage 链跳前应检查 subagent 工作是否完成"
status: pending
created_at: 2026-04-26
priority: high
---

harness next 当前实现：executing 退出后链式跳过 testing/acceptance/done 直达 done，因 testing/acceptance.exit_decision=verdict 触发 auto-jump 但**未检查这些 stage 的 subagent 工作是否实际完成**（例如 test-evidence.md / acceptance/checklist.md 是否产出）。req-43（交付总结完善）实证：一次 harness next 从 executing 跳到 done，跳过了独立 testing 和 acceptance 验证。建议给 verdict stage 加 'subagent 工作完成' gate 检查（如 test-evidence.md 存在 + 含 PASS/FAIL 结论）；未完成时不连跳，停在该 stage。
