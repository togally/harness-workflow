# Change

## 1. Title

审查并修正 catalog 文档的平台适配性

## 2. Goal

确保所有 `catalog/*.md` 中的工具描述、调用方式与当前 Claude Code / Codex / Qoder 平台的行为一致，无过时或误导性信息。

## 3. Requirement

- `req-24`

## 4. Scope

**包含：**
- 审查 `catalog/find-skills.md` 的调用方式描述
- 审查所有 catalog 文档中的"适用场景"和"不适用场景"
- 修正与当前 agent 平台不匹配的描述

**不包含：**
- 修改工具系统的整体架构文档（如 `index.md`、`selection-guide.md`）
- 新增或删除工具定义

## 5. Verification

- `find-skills.md` 中描述的调用方式与 Claude Code `Skill` 工具对齐
- 所有 catalog 文档无明显的平台适配性错误
