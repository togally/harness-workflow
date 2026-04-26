---
id: sug-37
title: "harness enter 应同步 runtime stage 到目标 req 真实值"
status: pending
created_at: 2026-04-26
priority: medium
---

harness enter <req-id> 后 runtime.yaml 的 stage / operation_type / operation_target 仍残留前任务（如归档后的 bugfix）字段。bugfix-6 归档后 enter req-43 实证：runtime stage=done 不动，与 req-43 state yaml stage=planning 不一致。建议 enter 命令同步从目标 req state yaml 读 stage 字段写回 runtime；同步 operation_type/target。
