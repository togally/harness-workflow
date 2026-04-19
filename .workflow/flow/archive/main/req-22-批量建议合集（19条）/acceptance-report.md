# req-22 验收报告

需求 ID: req-22  
标题: 批量建议合集（19条）  
验收阶段: acceptance  
验收日期: 2026-04-15  
验收员: 验收 agent

---

## 验收标准核对

### 标准 1：`harness suggest --apply-all` 只创建 1 个需求
- **结果**: 通过
- **证据**:
  - `src/harness_workflow/core.py` 第 3006-3068 行 `apply_all_suggestions()` 函数首行注释明确声明 `# 本函数强制将所有 pending suggest 打包为单一需求`，第 3032 行注释 `# 强制只创建 1 个需求，无论 pending 数量多少`，且函数体内仅调用一次 `create_requirement(root, title)`。
  - `test-report.md` 中记录了临时目录验证结果：创建 3 个假 suggest 后执行 `--apply-all`，仅生成 1 个需求目录 `req-11-测试打包`，suggest 池被清空。

### 标准 2：`suggest-conversion.md` 存在且包含 4 条核心规则和无例外声明
- **结果**: 通过
- **证据**:
  - 文件 `.workflow/constraints/suggest-conversion.md` 存在。
  - 包含 4 条核心规则（单一需求打包、禁止逐条独立需求、requirement.md 必须包含标题和摘要列表、违反视为 regression）。
  - 包含明确的"无例外"声明：`无例外。即使 suggest 数量再多、主题差异再大，也必须打包为一个需求，在需求内部通过变更拆分来处理。`

### 标准 3：`planning.md` 和 `review-checklist.md` 中已注入 suggest 打包约束检查
- **结果**: 通过
- **证据**:
  - `.workflow/context/roles/planning.md` 第 56 行"完成前必须检查"中新增第 5 项：`若本次变更涉及 suggest 批量转换，必须确认已阅读 .workflow/constraints/suggest-conversion.md，并确保所有 suggest 被打包为单一需求。`
  - `.workflow/context/checklists/review-checklist.md` 第 62 行 Constraints 层新增高优先级检查项：`[高] suggest 批量转换操作是否遵守 .workflow/constraints/suggest-conversion.md 的打包要求`

### 标准 4：3 个 skill 文件中均已添加 `harness suggest --apply-all` 强制打包要求
- **结果**: 通过
- **证据**:
  - `.claude/skills/harness/SKILL.md` 第 47-53 行包含 `### harness suggest --apply-all 强制打包要求` 章节。
  - `.qoder/skills/harness/SKILL.md` 第 47-53 行包含相同章节。
  - `.codex/skills/harness/SKILL.md` 第 47-53 行包含相同章节。
  - 三个文件均明确要求：检查约束文件、确保打包为单一需求、禁止手写脚本逐条创建、requirement.md 必须包含标题和摘要列表。

---

## 测试报告确认

- **test-report.md 总体判定**: 通过
- 测试报告中 chg-01、chg-02、chg-03 三项变更判定均为通过，无新增测试失败，无冲突或遗漏。

---

## 抽样验证记录

| 抽样文件 | 验证内容 | 结果 |
|---------|---------|------|
| `src/harness_workflow/core.py` | `apply_all_suggestions()` 强制打包逻辑与注释 | 通过 |
| `.workflow/constraints/suggest-conversion.md` | 4 条核心规则 + 无例外声明 | 通过 |
| `.claude/skills/harness/SKILL.md` | `--apply-all` 强制打包要求章节 | 通过 |
| `.qoder/skills/harness/SKILL.md` | `--apply-all` 强制打包要求章节 | 通过 |
| `.codex/skills/harness/SKILL.md` | `--apply-all` 强制打包要求章节 | 通过 |
| `.workflow/context/roles/planning.md` | suggest 批量转换约束检查项 | 通过 |
| `.workflow/context/checklists/review-checklist.md` | suggest 批量转换高优先级检查项 | 通过 |

---

## 总体结论

**验收通过。**

req-22 的所有变更产物均符合验收标准，测试报告判定为通过，无遗留问题。
