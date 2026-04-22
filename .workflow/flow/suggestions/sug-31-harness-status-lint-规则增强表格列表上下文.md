---
id: sug-31
title: harness status --lint 规则增强——识别表格/列表上下文，消假阳性
status: pending
created_at: "2026-04-21"
priority: medium
---

# 背景

req-31（批量建议合集（20条））chg-01 Step 3 落地 `harness status --lint` 后，对 req-31 自身产出目录扫出 **133 条契约 7 违规**。深入分析：多为 req-31 requirement.md §6 合并建议清单 / done-report.md §改进建议 等场景的"- sug-XX: title"枚举行——这些是表格/列表上下文中对 id 的紧凑引用，**不应算作契约 7 违规**。

testing / acceptance 已判"按 legacy fallback 接受"，但这是暂时性判定，长期应增强 lint 工具。

# 建议

`src/harness_workflow/validate_contract.py::check_contract_7` 识别以下 context 不算违规：

1. Markdown 表格行（`| ... | sug-XX | ... |`）
2. Markdown 列表项且同行含"- sug-XX:"/"- sug-XX（title）"/"- sug-XX 说明"等枚举格式
3. 代码块内（` ``` ... ``` `）的 id（不是文字引用）
4. 行内 code（`` `sug-XX` ``）
5. reference-style link 的 id（`[text][sug-XX]`）

以及：

- 对 heading（`## sug-XX`）仍要求首次命中带 title
- 连续 id 枚举（`sug-08 / sug-09 / sug-10`）只校验首个

# 影响

- lint 工具准确率大幅提升，可真正作为 CI gate
- 减少 legacy 文档的误报负担

# 关联

- `src/harness_workflow/validate_contract.py` `check_contract_7`
- `tests/test_contract7_lint.py`
- req-31（批量建议合集（20条））test-evidence.md AC-自证 ⚠️ 条目
