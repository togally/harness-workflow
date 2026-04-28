---
id: sug-54
title: "executing role briefing 应规定 ✅ marker（chg-01 executing 用 [x] gate 卡住）"
status: pending
created_at: 2026-04-28
priority: medium
---

req-46 chg-01 executing 阶段在完成 plan.md 各步骤后用 [x] 标 marker，但 work-done gate 期望的是 ✅ marker 文本，导致连续两次 harness next 被误判 'executing 工作未完成'。建议：base-role 或 executing.md 加 SOP 检查点：'plan.md 完成 marker 必须为 ✅（U+2705）而非 [x]'；或 _is_stage_work_done 兼容 [x] / ✓ / DONE 等多种 marker。来源：req-46 chg-01 executing 现场，session-memory 记录用户两次拉到才意识到。
