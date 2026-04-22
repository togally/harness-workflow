---
id: sug-45
title: CTO 派发 regression 场景加入 regression-specific default index 集
status: pending
created_at: "2026-04-22"
priority: low
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）/ chg-03（CTO 派发 briefing 注入 task_context_index + 快照落盘）扩展的 `_build_task_context_index` 当前按 stage 产出默认集。对 regression 场景（`stage="regression"`），默认集可以更聚焦：

- `.workflow/context/roles/regression.md`（当前 stage 角色）
- `.workflow/context/experience/roles/regression.md`
- `.workflow/context/experience/risk/known-risks.md`（回归时必读风险库）
- `.workflow/constraints/recovery.md`（失败恢复路径）

当前实现可能遗漏 `known-risks.md` 这种 regression 高相关条目。

# 建议

在 `_build_task_context_index` 内加入 stage-specific 额外集：

```python
if stage == "regression":
    candidates.append((".workflow/context/experience/risk/known-risks.md", "regression 风险库"))
```

类似地，testing 阶段可额外推 `known-risks.md`，acceptance 阶段可额外推 `review-checklist.md`。

# 验收

- regression 派发的 briefing 含 `known-risks.md`
- 现有 testing / acceptance 默认集不回归
- TDD 单测覆盖每个 stage specific 默认集
