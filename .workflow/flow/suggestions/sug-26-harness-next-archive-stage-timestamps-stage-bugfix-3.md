---
id: sug-26
title: "harness next/archive 联动写 stage_timestamps + stage（治 bugfix-3 复发）"
status: pending
created_at: 2026-04-25
priority: medium
---

harness next / harness archive 必须联动更新 req yaml stage 字段 + stage_timestamps；本 session req-38/40/41 三 req 都见 runtime stage vs req yaml stage 不同步现象（archive 残留、limbo 等）
