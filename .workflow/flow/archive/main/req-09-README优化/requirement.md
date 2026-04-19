# Requirement

## 1. Title

README 优化

## 2. Goal

当前仓库根目录的 `README.md` 内容不够聚焦，包含了过时的目录结构说明，实践原则和详细规则位置的引导不够清晰，且缺少对 `harness install --force` 强制安装的介绍。本需求的目标是优化 README，使其更简洁、重点更突出、引导更清晰。

## 3. Scope

**包含**：
- 调整 README 中"实践原则"部分的表述和位置
- 明确"详细规则位置"的引导说明
- 移除 README 中的目录结构说明（改为引用 `.workflow/` 内的相关文档即可）
- 在安装说明中新增"强制安装"的使用场景和命令

**不包含**：
- 修改 `.workflow/` 内部文档的内容
- 修改代码逻辑

## 4. Acceptance Criteria

- [ ] README 中的"实践原则"部分表述清晰、位置合理
- [ ] README 明确引导用户到 `.workflow/` 下查找详细规则
- [ ] README 中不再包含详细的目录结构列表
- [ ] README 的安装说明中包含强制安装的描述

## 5. Split Rules

### chg-01 README 内容重构

直接修改根目录 `README.md`：
- 重写或调整"实践原则"段落
- 增加"详细规则位置"引导段落
- 删除原有"目录结构"详细列表
- 在"安装"部分增加 `harness install --force` 的说明
