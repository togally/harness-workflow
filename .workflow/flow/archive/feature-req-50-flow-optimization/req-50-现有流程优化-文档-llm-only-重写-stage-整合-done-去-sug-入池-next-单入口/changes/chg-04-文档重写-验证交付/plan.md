---
id: chg-04
title: 文档 LLM-only 重写第二批：验证 / 交付文档
requirement: req-50
operation_type: plan
---

# Change Plan

## 1. Development Steps

### Step 1：diagnosis.md.tmpl 重写

- 当前 14 行（已紧凑）；新形态加 frontmatter：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  created_at: {{DATE}}
  operation_type: diagnosis
  verdict: pending
  ---

  # Regression Diagnosis

  ## 1. Issue
  - {{TITLE}}

  ## 2. Root Cause
  - {{由 regression 填}}

  ## 3. Routing
  - [ ] 真实问题 → 继续修复
  - [ ] 误判 → 回到上一阶段

  ## 4. Required Inputs
  - {{人工输入项}}

  ## 5. 测试用例设计
  > regression_scope: targeted
  > 波及接口清单：
  > - {{file/function}}

  | 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
  |---|---|---|---|---|
  ```
- `.en.tmpl` 同步。

### Step 2：regression-decision.md.tmpl 重写

- 新形态：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  created_at: {{DATE}}
  operation_type: regression-decision
  verdict: {confirm|reject|escalate}
  next_stage: {planning|executing|testing|acceptance|done}
  ---

  # Regression Decision

  ## 1. Verdict
  - {{决策结论}}

  ## 2. Reasoning
  - {{支撑理由 bullet}}

  ## 3. Next Action
  - {{下一步动作}}
  ```
- `.en.tmpl` 同步。

### Step 3：regression-required-inputs.md.tmpl + regression-analysis.md.tmpl + regression.md.tmpl 重写

- regression-required-inputs.md.tmpl：frontmatter `id` / `title` / `created_at` / `operation_type: required-inputs` + body 「## Required Inputs」单段 bullet。
- regression-analysis.md.tmpl：frontmatter + 「## Hypothesis / ## Evidence / ## Conclusion」三段 bullet。
- regression.md.tmpl：frontmatter `id` / `title` / `created_at` / `operation_type: regression` / `routed_from` / `routed_to` + body 「## Issue / ## Routing / ## Status」三段。
- 全部 `.en.tmpl` 同步。

### Step 4：test-cases.md.tmpl + test-plan.md.tmpl 重写

- test-cases.md.tmpl：frontmatter + 「## Test Cases」单段表格（保留 `用例名` / `输入` / `期望` / `对应 AC` / `优先级` 列名）。
- test-plan.md.tmpl：frontmatter + 「## Scope / ## Cases / ## Verification」三段。

### Step 5：acceptance-checklist.md.tmpl 重写

- 当前 16 行（已含表格）；新形态加 frontmatter：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  created_at: {{DATE}}
  operation_type: acceptance-checklist
  verdict: pending
  ---

  # Acceptance Checklist

  ## 1. Reference
  - requirement_link: {{path}}

  ## 2. Checklist
  | # | Item | Basis | Result | Notes |
  |---|---|---|---|---|

  ## 3. Sign-off
  - reviewer: {{name}}
  - date: {{date}}
  - verdict: {pass|fail}
  ```

### Step 6：requirement-completion.md.tmpl 重写

- 新形态 frontmatter `id` / `title` / `created_at` / `operation_type: completion` / `verdict` + body 「## Delivered / ## Verification / ## Sign-off」三段。
- `.en.tmpl` 同步。

### Step 7：done.md / acceptance.md / testing.md inline 模板段改写

- `.workflow/context/roles/done.md` 内「最小字段模板（交付总结.md）」段：保留 §需求是什么 / §交付了什么 / §结果是什么 / §后续建议 / §效率与成本（含「总耗时 / 总 token / 各阶段切片」三表），删除每段下的「示例 / 解释」prose（如有）。
- 同款处理「bugfix 交付总结模板（精简版）」段。
- `.workflow/context/roles/testing.md`（如有 inline 模板段）：保留 test-report.md / test-evidence.md 结构化字段，删除冗余 prose。
- `.workflow/context/roles/acceptance.md`（如有 inline 模板段）：同上。

### Step 8：模板文件 frontmatter 占位符校验

- 全 14+ 文件 grep `^id: \{\{ID\}\}` / `^title: \{\{TITLE\}\}` / `^operation_type:` 各命中 ≥ 1。
- yaml.safe_load 解析每个填充后产物（用伪造 ID / TITLE）成功。

### Step 9：grep 自检

- `grep -lE "^## .*(背景|历史|修订说明|用户原话|设计理念|演进)" .claude/skills/harness/assets/templates/*.tmpl .workflow/context/roles/*.md` 命中 = 0（除本 req-50 自身 requirement.md 含「§2.3 优化策略总览」中无背景词）。

## 2. Verification Steps

### 2.1 单元测试 / 静态核对

- `wc -l` 对比每个模板新旧行数：除 diagnosis.md.tmpl / acceptance-checklist.md.tmpl 已紧凑（豁免）外，其余 ≥ 50% 压缩。
- frontmatter 字段断言：每个 .tmpl 首部含 `---` + 至少 4 个必填字段（`id` / `title` / `created_at` / `operation_type`）。
- pytest 现有 test_create_regression / test_create_diagnosis 等 test 全绿。
- 新增 test_template_frontmatter.py：遍历 templates/ 目录，断言所有 .tmpl 文件首部 yaml.safe_load 解析成功（用伪填充 ID / TITLE）。

### 2.2 手工 smoke / 集成验证

- tmpdir 跑 `harness regression "test issue"` → 检查 `regression.md` / `diagnosis.md` 含正确 frontmatter。
- tmpdir 跑 testing / acceptance 阶段（dogfood）：产出 `test-report.md` / `acceptance-report.md` 含正确字段。
- tmpdir 跑 done 阶段：产出 `交付总结.md` 含 §效率与成本三表（保留旧字段名）。

### 2.3 AC 映射

- AC-01 → Step 1 ~ Step 7 + 2.1 grep。
- AC-02 → Step 1 ~ Step 7 + 2.1 wc + frontmatter 字段断言。
- AC-11 → 不动归档历史；2.1 默认满足。

## 3. 依赖与执行顺序

- 依赖 chg-01：稳定 stage 名（虽然本 chg 模板 frontmatter 不直接含 stage 名，但 diagnosis.md / regression-decision.md 的 `next_stage` 字段取值需与 chg-01 后的 sequence 一致）。
- 依赖 chg-03：chg-03 建立的 frontmatter 占位符（`{{SLUG}}` / `{{OPERATION_TYPE}}`）+ helper（`_yaml_escape`）+ 测试 fixture 在本 chg 复用。
- 与 chg-03 实操可并行（plan 上硬序 chg-03 → chg-04 但无强代码冲突）。
- 内部硬序：Step 1 ~ Step 6（10 个模板可并行写）→ Step 7（inline 模板段）→ Step 8 ~ Step 9（自检）。

## 4. 测试用例设计

> regression_scope: targeted  # 仅改模板 + inline role 段；不动核心 helper / sequence
> 波及接口清单：
> - `.claude/skills/harness/assets/templates/diagnosis.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/regression-decision.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/regression-required-inputs.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/regression-analysis.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/regression.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/test-cases.md.tmpl`
> - `.claude/skills/harness/assets/templates/test-plan.md.tmpl`
> - `.claude/skills/harness/assets/templates/acceptance-checklist.md.tmpl`
> - `.claude/skills/harness/assets/templates/requirement-completion.md.tmpl` + `.en.tmpl`
> - `.workflow/context/roles/done.md::最小字段模板` inline 段
> - `.workflow/context/roles/done.md::bugfix 交付总结模板（精简版）` inline 段
> - `.workflow/context/roles/testing.md::test-report.md 模板` inline 段（如有）
> - `.workflow/context/roles/acceptance.md::acceptance-report.md 模板` inline 段（如有）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|---|---|---|---|---|
| TC-01 | grep `^## .*(背景\|历史\|修订说明\|用户原话\|设计理念\|演进)` 在所有 14 个 .tmpl + 4 个 inline 段 | 命中 = 0 | AC-01 | P0 |
| TC-02 | `head -10 diagnosis.md.tmpl` | 含 `---` frontmatter + `id:` / `title:` / `operation_type: diagnosis` / `verdict: pending` | AC-02 | P0 |
| TC-03 | `head -10 regression-decision.md.tmpl` | 含 `verdict:` + `next_stage:` 字段 | AC-02 | P0 |
| TC-04 | `wc -l acceptance-checklist.md.tmpl` | 行数 ≤ 22（原 16 + frontmatter 6 行） | AC-02 | P1 |
| TC-05 | `wc -l requirement-completion.md.tmpl` | 行数压缩 ≥ 50%（与 git history 旧版对比） | AC-02 | P1 |
| TC-06 | yaml.safe_load 解析每个 .tmpl 填充后产物（伪 ID/TITLE） | 全部解析成功 | AC-02 | P0 |
| TC-07 | done.md inline `## 最小字段模板` 段 | 保留 §效率与成本三表（总耗时 / 总 token / 各阶段切片）；无「示例 / 背景」prose | AC-01 + AC-02 | P0 |
| TC-08 | done.md inline `## bugfix 交付总结模板（精简版）` 段 | 保留 §修复验证段；无「示例」prose | AC-01 + AC-02 | P0 |
| TC-09 | tmpdir `harness regression "test"` | regression.md / diagnosis.md 创建成功且 frontmatter 完整 | AC-02 | P0 |
| TC-10 | tmpdir 跑 testing 阶段 dogfood | `test-report.md` / `test-evidence.md` 内字段名（如 `用例数 / PASS 数 / 跑出 N passed`）保留不变 | AC-02 + AC-11 | P0 |
| TC-11 | grep 历史 archive/ 目录 acceptance-report.md / test-report.md | 内容与 git history 一致（未改写） | AC-11 | P0 |
| TC-12 | 双语 .en.tmpl 字段名 | 与中文版一致；body 段英文 | AC-02 | P1 |
| TC-13 | yaml.safe_load `verdict: pending` / `verdict: pass` 解析 | 解析为 `"pending"` / `"pass"` 字符串（未被识别为 yaml bool / null） | AC-02 | P0 |
