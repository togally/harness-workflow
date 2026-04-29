---
id: chg-03
title: 文档 LLM-only 重写第一批：核心机器型文档
requirement: req-50
created_at: 2026-04-29
operation_type: change
---

# Change

## 1. Title

文档 LLM-only 重写（第一批：核心机器型）（O1 part 1）

## 2. Goal

把现有 5 类核心机器型文档模板（`bugfix.md` / `requirement.md` / `change.md` / `plan.md` / `session-memory.md`）改为「YAML frontmatter（结构化字段，LLM 直读）+ 紧凑 markdown（prose 用 bullet）」形态（D1 = B），删除所有「对人解释」段落（背景 / 历史 / 用户原话引用 / 修订说明 / 设计理念），保留：变更前后状态、验证证据、流转决策、AC 映射、id+title 引用契约。

## 3. Requirement

- `req-50（现有流程优化：文档 LLM-only 重写 + stage 整合 + done 去 sug 入池 + next 单入口）`
- 关联 AC：AC-01 / AC-02 / AC-11

## 4. Scope

### Included

5 类模板文件（共 10 个 .tmpl，含 .en 双语）：

- `.claude/skills/harness/assets/templates/requirement.md.tmpl` + `.en.tmpl`
- `.claude/skills/harness/assets/templates/change.md.tmpl` + `.en.tmpl`
- `.claude/skills/harness/assets/templates/change-plan.md.tmpl` + `.en.tmpl`（注意当前文件名是 `change-plan` 不是 `plan`）
- `.claude/skills/harness/assets/templates/session-memory.md.tmpl` + `.en.tmpl`
- `.claude/skills/harness/assets/templates/bugfix.md.tmpl` + `.en.tmpl`

每个模板新形态：

```markdown
---
id: {{ID}}
title: {{TITLE}}
created_at: {{DATE}}
operation_type: {requirement|change|plan|session-memory|bugfix}
slug: {{SLUG}}
[领域字段：requirement: 无；change: requirement; plan: requirement; bugfix: severity, root_cause]
---

# {领域标题}

## 1. {主结构字段 1}
- {bullet}

## 2. {主结构字段 2}
- {bullet}

[...]
```

**删除内容硬清单**（grep 自检）：

- 任何含「## 背景」「## 历史」「## 修订说明」「## 用户原话」「## 设计理念」「## 为什么」标题的段落。
- 任何 `<!-- 示例：-->` HTML 注释中含「对人解释 / 背景说明 / 演进历史」字样的（保留纯字段说明注释如「示例：列出本 change 要做的事」）。
- 任何 prose 段超过 3 行「叙事性描述」（连续非 bullet 行）。

**保留内容硬清单**：

- 变更前后状态（如 requirement.md 的 §3 Scope In/Out / change.md 的 §4 Scope Included/Excluded）。
- 验证证据字段（plan.md 的 §2 Verification Steps、§4 测试用例设计）。
- 流转决策字段（session-memory.md 的「下一步」「待确认问题」）。
- AC 映射（plan.md §2.3 AC 映射 / change.md §5 Acceptance）。
- id+title 引用契约（首次引用形如 `{id}（{title}）`）。

**新增 frontmatter 必填字段**：

- `id`（如 `req-50` / `chg-01` / `bugfix-7`）
- `title`（一句话标题）
- `created_at`（ISO 日期）
- `operation_type`（取值 `requirement` / `change` / `plan` / `session-memory` / `bugfix`）
- `slug`（用于路径，URL-safe）
- 领域特定字段：bugfix.md 加 `severity` / `root_cause`；change.md 加 `requirement` 反向引用；plan.md 加 `requirement`。

### Excluded

- 不动测试 / 验收 / 交付类模板（chg-04 处理：test-evidence.md / acceptance-report.md / acceptance-checklist.md / 交付总结.md / bugfix-交付总结.md / diagnosis.md 等）。
- 不动 `change-meta.yaml` / `requirement-meta.yaml` 等已是 yaml 的元数据文件（无需重写）。
- 不动 `.workflow/flow/` 下已存在的历史 req（req-02 ~ req-49）/ bugfix（bugfix-1 ~ N）的 requirement.md / change.md / plan.md（D5 = B 仅未来生效）。
- 不动 CLI 写入 helper（如 `create_requirement` / `create_change`），它们读模板 .tmpl 并填占位符的逻辑保持兼容（YAML frontmatter 占位符填充逻辑由 chg-05 dogfood 验证）。

## 5. Acceptance

- 覆盖 AC-01：5 类模板（含双语 10 个 .tmpl 文件）grep `## .*背景\|## .*历史\|## .*修订说明\|## .*用户原话\|## .*设计理念` 命中 = 0。
- 覆盖 AC-02：每个新模板 head 含 5 个必填 frontmatter 字段（`id` / `title` / `created_at` / `operation_type` / `slug`）；行数 ≤ 原模板 50%（统一阈值，单模板可放宽到 60%，但全 10 文件平均 ≤ 50%）。
- 覆盖 AC-11：grep `req-02 ~ req-49` 归档目录的 requirement.md 内容未被改写（diff 应为 0 行 changed）。

## 6. Risks

- 风险：CLI 占位符填充逻辑（`{{TITLE}}` / `{{ID}}` / `{{DATE}}`）与新 frontmatter 字段不兼容，导致 `harness requirement` / `harness change` 创建失败。
  缓解：模板新增 frontmatter 占位符 `{{ID}}` / `{{TITLE}}` / `{{DATE}}` / `{{SLUG}}` / `{{OPERATION_TYPE}}`，CLI helper 同步注入；chg-05 dogfood e2e 验证。
- 风险：YAML frontmatter 解析失败（如包含特殊字符）。
  缓解：占位符填充时对 `title` / `slug` 做 yaml-escape；新增 helper `_yaml_escape(s) -> str`。
- 风险：双语模板（.en.tmpl）frontmatter 字段名是否本地化。
  缓解：默认英文字段名（`id` / `title` / `created_at` / `operation_type` / `slug`）双语共用；body 段中文模板用中文标题，英文用英文标题。
