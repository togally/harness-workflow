---
id: sug-29
title: flow/stages.md 文档（6 阶段）与 WORKFLOW_SEQUENCE 代码（8 阶段）断层
status: pending
created_at: "2026-04-21"
priority: medium
---

# 背景

`.workflow/flow/stages.md` 描述 workflow 为 6 阶段：`requirement_review → planning → executing → testing → acceptance → done`，但 `src/harness_workflow/workflow_helpers.py:101 WORKFLOW_SEQUENCE` 实际为 8 阶段：`requirement_review → changes_review → plan_review → ready_for_execution → executing → testing → acceptance → done`。

缺失 3 个审查关：`changes_review` / `plan_review` / `ready_for_execution`。req-30（slug 沟通可读性增强：全链路透出 title）ff 运行时主 agent 按 6 阶段文档编排，实际上**跳过了 3 个 review 关**；req-31（批量建议合集（20条））ff 运行时通过 `harness next` CLI 才发现真实 8 阶段。

此外 `stage: "planning"` 这个值根本不在 WORKFLOW_SEQUENCE 里，但 `harness next` 未拒绝——另一个潜在 bug。

# 建议

1. **同步 stages.md 到 8 阶段**：补 `changes_review` / `plan_review` / `ready_for_execution` 三个 stage 的定义（入口/出口/必须产出/下一步）
2. **新建 stage 校验**：`workflow_helpers.py` 在 runtime.yaml 读取 stage 时断言该值 ∈ WORKFLOW_SEQUENCE，否则报错
3. **补角色文件**：`context/roles/` 下有 `planning.md` 但没有 `changes_review.md` / `plan_review.md` / `ready_for_execution.md`——决定是否合并还是拆分
4. **废弃"planning" 别名**：若历史遗留代码用 `planning` stage，加 deprecation warning

# 关联

- `.workflow/flow/stages.md`
- `src/harness_workflow/workflow_helpers.py:101 WORKFLOW_SEQUENCE`
- `.workflow/context/roles/planning.md`
- req-30（slug 沟通可读性增强：全链路透出 title）ff 运行历史
- req-31（批量建议合集（20条））ff 运行历史
