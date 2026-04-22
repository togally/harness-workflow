---
id: sug-12
title: "harness next 从 executing → testing 有时一次推两个子阶段"
status: pending
created_at: 2026-04-22
priority: high
---

本轮 req-29 从 executing 跑 harness next，一次调用产生 'Workflow advanced to testing' + 'Workflow advanced to acceptance' 两条输出，testing 子阶段被吞合。导致 testing subagent 未被独立派发，最终把 testing 职责合并到 acceptance subagent 完成。与 req-28 sug-09（acceptance → done 需重试两次）同类不同触发路径。建议统一排查 stage 推进的幂等 + 原子性，加单元测试覆盖每个 stage 单步推进。
