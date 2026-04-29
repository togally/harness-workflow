---
id: chg-03
title: 文档 LLM-only 重写第一批：核心机器型文档
requirement: req-50
operation_type: plan
---

# Change Plan

## 1. Development Steps

### Step 1：requirement.md.tmpl 重写

- 当前模板（`requirement.md.tmpl` 26 行）：保留 §1 Title / §2 Goal / §3 Scope / §4 AC / §5 拆分要求；删除「对人解释」类注释。
- 新模板形态：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  created_at: {{DATE}}
  operation_type: requirement
  slug: {{SLUG}}
  ---

  # Requirement

  ## 1. Title
  {{TITLE}}

  ## 2. Goal
  - {{一句话目标}}

  ## 3. Scope
  ### In
  - {{覆盖项}}
  ### Out
  - {{不做项}}

  ## 4. Acceptance Criteria
  | AC | 关联 | 验收口径 |
  |---|---|---|
  | AC-01 | {{优化项}} | {{断言}} |

  ## 5. Split Rules
  - 拆分为多个独立交付的 chg
  - 每个 chg 覆盖单一可独立验收的功能点
  ```
- 双语 `.en.tmpl` 同步重写。

### Step 2：change.md.tmpl 重写

- 当前模板 36 行；新模板压缩到 ≤ 18 行 body。
- 新模板形态：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  requirement: {{REQUIREMENT_ID}}
  created_at: {{DATE}}
  operation_type: change
  ---

  # Change

  ## 1. Title
  {{TITLE}}

  ## 2. Goal
  - {{一句话目标}}

  ## 3. Scope
  ### Included
  - {{交付项}}
  ### Excluded
  - {{不做项}}

  ## 4. Acceptance
  - 覆盖 AC-XX：{{断言}}

  ## 5. Risks
  - 风险：{{描述}}；缓解：{{措施}}
  ```
- 双语 `.en.tmpl` 同步重写。

### Step 3：change-plan.md.tmpl 重写

- 当前模板 49 行；新模板 ≤ 25 行 body。
- 新模板形态：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  requirement: {{REQUIREMENT_ID}}
  operation_type: plan
  ---

  # Change Plan

  ## 1. Development Steps
  ### Step 1：{{标题}}
  - {{动作}}

  ## 2. Verification Steps
  ### 2.1 Static
  - {{grep / diff 断言}}
  ### 2.2 Smoke
  - {{e2e 步骤}}
  ### 2.3 AC 映射
  - AC-XX → Step X + 2.X

  ## 3. Dependencies
  - {{依赖说明}}

  ## 4. 测试用例设计
  > regression_scope: targeted
  > 波及接口清单：
  > - {{file/function}}

  | 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
  |---|---|---|---|---|
  | TC-01 | ... | ... | AC-01 | P0 |
  ```
- 双语 `.en.tmpl` 同步重写。

### Step 4：session-memory.md.tmpl 重写

- 当前模板 46 行（含「待处理捕获问题」表格）；新模板 ≤ 25 行 body。
- 新模板形态：
  ```markdown
  ---
  id: {{ID}}
  stage: {{STAGE}}
  created_at: {{DATE}}
  operation_type: session-memory
  ---

  # Session Memory

  ## 1. Goal
  - {{当前目标}}

  ## 2. Status
  - {{完成内容}}

  ## 3. Verified
  - {{已验证可行项}}

  ## 4. Dead Ends
  - 尝试：{{尝试}}；失败：{{原因}}；提醒：{{回避路径}}

  ## 5. Next
  - {{下一步}}

  ## 6. Open Questions
  - {{待确认}}

  ## 7. Captured Out-of-Scope
  | # | 来源 | 描述 | 状态 |
  |---|---|---|---|
  ```
- 双语 `.en.tmpl` 同步重写。

### Step 5：bugfix.md.tmpl 重写

- 当前模板 31 行（已含 frontmatter `id` / `title` / `created_at`）；新模板 ≤ 22 行 body，frontmatter 扩展。
- 新模板形态：
  ```markdown
  ---
  id: {{ID}}
  title: {{TITLE}}
  created_at: {{DATE}}
  operation_type: bugfix
  slug: {{SLUG}}
  severity: {{SEVERITY}}
  root_cause: {{ROOT_CAUSE_PENDING}}
  ---

  # Bugfix

  ## 1. Symptom
  - 现象：{{描述}}
  - 触发条件：{{条件}}
  - 影响范围：{{范围}}

  ## 2. Root Cause
  - 根因：{{由 regression 填}}
  - 真实问题 / 误判：{{routing}}

  ## 3. Fix Scope
  ### Included
  - {{文件/模块}}
  ### Excluded
  - {{不修}}

  ## 4. Fix Plan
  - 步骤：{{动作}}

  ## 5. Verification
  - {{验证项}}
  ```
- 双语 `.en.tmpl` 同步重写。

### Step 6：CLI helper 占位符注入更新

- `src/harness_workflow/workflow_helpers.py`：`create_requirement` / `create_change` / `create_bugfix` 调用模板填充时，新增占位符替换：
  - `{{SLUG}}` → 由 `_slugify(title)` 生成。
  - `{{OPERATION_TYPE}}` → 字面量按 helper 类型注入。
- 新增 `_yaml_escape(s)` helper：替换 `:` `"` `\n` 等 yaml 特殊字符；用于 `title` 字段填充。
- pytest 已有 test_create_requirement / test_create_change / test_create_bugfix 跑通新模板。

### Step 7：grep 自检

- 全 10 .tmpl 文件 grep `## .*背景\|## .*历史\|## .*修订说明\|## .*用户原话\|## .*设计理念\|## .*为什么` 命中 = 0。
- 全 10 文件行数对比 Git history 旧版：平均 ≤ 50% 原行数。

## 2. Verification Steps

### 2.1 单元测试 / 静态核对

- `wc -l` 对比新旧模板行数：
  - requirement.md.tmpl: 26 → ≤ 18
  - change.md.tmpl: 36 → ≤ 18
  - change-plan.md.tmpl: 49 → ≤ 25
  - session-memory.md.tmpl: 46 → ≤ 25
  - bugfix.md.tmpl: 31 → ≤ 22
- `grep -lE "^## .*(背景|历史|修订说明|用户原话|设计理念|为什么)" .claude/skills/harness/assets/templates/*.tmpl` 命中 = 0。
- 每个 .tmpl 文件首部含 frontmatter `---` 块，必填字段 `id` / `title` / `created_at` / `operation_type` / `slug`（除 `change-plan.md.tmpl` 不要 `slug`）。
- pytest 现有 test_create_*.py 全绿。

### 2.2 手工 smoke / 集成验证

- tmpdir 跑 `harness install` → `harness requirement "smoke req"`：
  - 检查 `.workflow/flow/requirements/{slug}/requirement.md` 含正确 frontmatter（id / title / created_at / operation_type=requirement / slug）。
  - 内容符合新模板结构（5 节，无背景 / 历史段）。
- 同理 `harness change` / `harness bugfix` 创建产物均符合新模板。

### 2.3 AC 映射

- AC-01 → Step 1 ~ Step 5 + 2.1 grep。
- AC-02 → Step 1 ~ Step 5 + 2.1 wc + frontmatter 字段断言。
- AC-11 → 不动归档历史（grep diff 验证）；2.1 默认满足（仅改 .tmpl 不动 archive/）。

## 3. 依赖与执行顺序

- 依赖 chg-01：稳定 stage 名（虽然本 chg 未直接引用 stage，但模板新增 frontmatter `operation_type` 取值需与 chg-01 后的语义一致）。
- 依赖 chg-02：done 去 sug 入池后，session-memory 模板不需「sug 入池」字段（如有）。
- 内部硬序：Step 1 ~ Step 5（5 个模板可并行写）→ Step 6（helper）→ Step 7（自检）。
- 与 chg-04 可并行（plan 上硬序 chg-03 → chg-04，但实操可同时改）。

## 4. 测试用例设计

> regression_scope: targeted  # 仅改模板 + helper 占位符；不改 sequence / schema 状态
> 波及接口清单：
> - `.claude/skills/harness/assets/templates/requirement.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/change.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/change-plan.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/session-memory.md.tmpl` + `.en.tmpl`
> - `.claude/skills/harness/assets/templates/bugfix.md.tmpl` + `.en.tmpl`
> - `src/harness_workflow/workflow_helpers.py::create_requirement`（占位符填充）
> - `src/harness_workflow/workflow_helpers.py::create_change`（占位符填充）
> - `src/harness_workflow/workflow_helpers.py::create_bugfix`（占位符填充）
> - `src/harness_workflow/workflow_helpers.py::_yaml_escape`（新增 helper）
> - `src/harness_workflow/workflow_helpers.py::_slugify`（已存在）

| 用例名 | 输入 | 期望 | 对应 AC | 优先级 |
|---|---|---|---|---|
| TC-01 | `wc -l requirement.md.tmpl` | 行数 ≤ 18（原 26） | AC-02 | P0 |
| TC-02 | `wc -l change.md.tmpl` | 行数 ≤ 18（原 36，压缩 ≥ 50%） | AC-02 | P0 |
| TC-03 | `wc -l change-plan.md.tmpl` | 行数 ≤ 25（原 49） | AC-02 | P0 |
| TC-04 | `wc -l session-memory.md.tmpl` | 行数 ≤ 25（原 46） | AC-02 | P0 |
| TC-05 | `wc -l bugfix.md.tmpl` | 行数 ≤ 22（原 31） | AC-02 | P0 |
| TC-06 | grep `^## .*(背景\|历史\|修订说明\|用户原话\|设计理念)` 在 5 个 .tmpl + 5 个 .en.tmpl | 命中 = 0 | AC-01 | P0 |
| TC-07 | `head -10 requirement.md.tmpl` 检查 frontmatter | 含 `---` + `id:` + `title:` + `created_at:` + `operation_type: requirement` + `slug:` | AC-02 | P0 |
| TC-08 | bugfix.md.tmpl frontmatter 含 `severity` + `root_cause` 字段 | grep 命中 ≥ 1 | AC-02 | P0 |
| TC-09 | tmpdir `harness requirement "test req with: special chars"` | 创建产物 frontmatter 中 `title:` 字段 yaml-escape 正确（无解析错误） | AC-02 | P0 |
| TC-10 | tmpdir `harness change "test change"` | `change.md` 含 `requirement: req-XX` 反向引用字段 | AC-02 | P1 |
| TC-11 | tmpdir `harness bugfix "test bug"` | `bugfix.md` 含 `severity: pending` 与 `root_cause: pending` 默认值 | AC-02 | P1 |
| TC-12 | grep 历史 req-46 archive 目录 `requirement.md` | 内容与 git history 一致（未改写，AC-11） | AC-11 | P0 |
| TC-13 | 双语 `.en.tmpl` frontmatter 字段名 | 与中文 `.tmpl` 一致（`id` / `title` / `created_at` / `operation_type` / `slug`） | AC-02 | P1 |
| TC-14 | yaml.safe_load 解析每个新模板填充后产物 | 全部解析成功（无 yaml ParseError） | AC-02 | P0 |
