---
id: chg-04
title: 文档 LLM-only 重写第二批：验证 / 交付文档
requirement: req-50
created_at: 2026-04-29
operation_type: change
---

# Change

## 1. Title

文档 LLM-only 重写（第二批：验证 / 交付）（O1 part 2）

## 2. Goal

把现有 6+ 类验证 / 交付类机器型文档模板（`test-evidence.md` / `acceptance-report.md` / `acceptance-checklist.md` / `交付总结.md` / `bugfix-交付总结.md` / `diagnosis.md` / `regression-decision.md` / `regression-required-inputs.md` / `test-cases.md` / `test-plan.md`）改为 YAML frontmatter + 紧凑 markdown 形态，删除「对人解释」段落，保留：用例 / 证据 / 验收结论 / 路由决策 / 效率成本表 / AC 映射。

## 3. Requirement

- `req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）`
- 关联 AC：AC-01 / AC-02 / AC-11

## 4. Scope

### Included

10 类模板文件 + 嵌入 done.md / acceptance.md / testing.md 内的 inline 模板：

**.tmpl 文件**（共 ~14 个，含 .en 双语）：

- `acceptance-checklist.md.tmpl`（无 .en，需补）
- `diagnosis.md.tmpl` + `.en.tmpl`
- `regression-decision.md.tmpl` + `.en.tmpl`
- `regression-required-inputs.md.tmpl` + `.en.tmpl`
- `regression-analysis.md.tmpl` + `.en.tmpl`
- `regression.md.tmpl` + `.en.tmpl`
- `test-cases.md.tmpl`（无 .en）
- `test-plan.md.tmpl`（无 .en）
- `requirement-completion.md.tmpl` + `.en.tmpl`

**inline 模板**（嵌入角色文件）：

- `.workflow/context/roles/done.md` 内「最小字段模板（交付总结.md）」段：保留结构化字段，删除冗余示例文字。
- `.workflow/context/roles/done.md` 内「bugfix 交付总结模板（精简版）」段：同上。
- `.workflow/context/roles/testing.md` 内「test-report.md / test-evidence.md 字段模板」段（如存在）：同上。
- `.workflow/context/roles/acceptance.md` 内「acceptance-report.md 字段模板」段（如存在）：同上。

**新形态共性**：

```markdown
---
id: {{ID}}                  # req-XX / chg-XX / bugfix-XX / reg-XX
title: {{TITLE}}
created_at: {{DATE}}
operation_type: {test-evidence|acceptance-report|diagnosis|regression-decision|...}
verdict: {pass|fail|pending}    # 仅验证类
---

# {领域标题}

## 1. {字段}
- bullet
```

**删除内容**：标题段含「## 背景 / 历史 / 修订说明 / 用户原话 / 设计理念 / 演进过程」全删；prose 段超过 3 行叙事改为 bullet。

**保留内容**：

- 用例字段（test-cases / test-plan / diagnosis §测试用例设计）。
- 证据字段（test-evidence / pytest 跑出 N passed / acceptance-report verdict）。
- 路由字段（diagnosis 路由方向 / regression-decision verdict + next_stage）。
- 效率成本表（done.md 交付总结模板 §效率与成本）。
- AC 映射 / id+title 引用契约。

### Excluded

- 不动 chg-03 已处理的 5 类核心机器型模板。
- 不动 `requirement-changes.md.tmpl` / `requirement-meta.yaml.tmpl` / `change-meta.yaml.tmpl` / `regression-meta.yaml.tmpl`（已是 yaml 元数据，无 prose 段需删）。
- 不动 `version-memory.md.tmpl` / `version-readme.md.tmpl` / `self-test.md.tmpl`（用途不在本 req 流程范围）。
- 不动归档历史 req / bugfix 已落地的对应文档（D5 = B 仅未来生效）。

## 5. Acceptance

- 覆盖 AC-01：所有 14+ 文件 grep `^## .*(背景|历史|修订说明|用户原话|设计理念|演进)` 命中 = 0；done.md / acceptance.md / testing.md 内 inline 模板段同样符合。
- 覆盖 AC-02：每个新模板含 frontmatter 必填字段（至少 `id` / `title` / `created_at` / `operation_type`）；行数压缩 ≥ 50%（diagnosis.md.tmpl 当前 14 行已紧凑，可豁免压缩；其他至少 50%）。
- 覆盖 AC-11：归档历史 archive/ 目录下对应文件未被改写。

## 6. Risks

- 风险：`acceptance-checklist.md.tmpl` 当前是 markdown 表格无 frontmatter，加 frontmatter 可能影响 reviewer 阅读。
  缓解：frontmatter 字段最小化（仅 `id` / `title` / `verdict: pending`），表格主体不动。
- 风险：done.md / acceptance.md / testing.md inline 模板段改写可能影响 done / acceptance / testing subagent 实际行为。
  缓解：保留所有结构化字段名（如 `## 总耗时` / `## 总 token` / `## 各阶段切片` 不改名），只删冗余示例 prose；chg-05 dogfood 验证。
- 风险：`test-cases.md.tmpl` / `test-plan.md.tmpl` 表格列名改动会破坏 testing 角色解析逻辑。
  缓解：保留现有列名（用例名 / 输入 / 期望 / 对应 AC / 优先级），只删表格上下解释 prose。
