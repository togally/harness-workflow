# Change

## 1. Title

端到端验证 toolsManager 查询流程

## 2. Goal

验证在 chg-01 和 chg-02 完成后，toolsManager 角色按 SOP 执行时，能够为各 stage 的常见操作意图正确匹配并推荐工具。

## 3. Requirement

- `req-24`

## 4. Scope

**包含：**
- 模拟 executing/testing/regression 等阶段的典型操作意图
- 按 toolsManager SOP 执行关键词匹配和评分排序
- 记录验证结果和发现的问题

**不包含：**
- 修改 toolsManager 的匹配算法
- 新增 catalog 工具

## 5. Verification

- 至少验证 6 个不同的操作意图查询
- 每个查询都能返回明确的 matched/not_found 结果
- 验证结果记录到本 change 的 session-memory.md
