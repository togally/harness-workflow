# Acceptance Stage Experience

> Placeholder experience file. Fill in based on actual project lessons.

## Key Constraints

<!-- Record must-follow constraints here -->

## Best Practices

<!-- Record recommended approaches here -->

## Common Mistakes

<!-- Record common errors here -->

## 经验一：harness validate --human-docs 的 Summary 口径以工具输出为准，不按 briefing 记忆硬编码

### 场景

req-29 briefing 预期"validate --human-docs 最终 18/18"，但工具实际输出 14/14（5 变更简报 + 5 实施说明 + 4 个 req 级对人文档）。

### 经验内容

- acceptance 与 done 阶段跑 `harness validate --human-docs --requirement <req-id>` 后，应**以工具实际输出的 Summary 为准**，不能按 briefing 或记忆里的期望数字硬断言。
- 若 briefing 预期数与实际输出不符，需在验收摘要.md / done-report.md 中如实记录实际数并说明差异原因（通常是 briefing 对条目数的估算不准，而不是落盘缺失）。
- 正确的硬门禁语义是"Summary 行必须包含 'All human docs landed.'"而不是"数字必须等于 N"。

### 反例

- 根据 briefing 的 18/18 预期死磕工具，误判 validate 失败。
- 在 acceptance/done 报告里写错期望数，导致后续审阅者 confused。

### 来源

req-29 — ff --auto + archive 路径清洗批量合集
