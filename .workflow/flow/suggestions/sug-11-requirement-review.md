---
id: sug-11
title: "requirement-review 阶段增加仓库路径存在性自检"
status: pending
created_at: 2026-04-22
priority: medium
---

本轮 req-28 的 requirement.md 把 .workflow/archive/ 误写成 .workflow/flow/archive/，直到 changes_review 才由架构师发现。建议 requirement-review 退出前对 requirement.md 中引用的仓库路径做 ls / git ls-files 验证，避免 planning 阶段才暴露笔误。
