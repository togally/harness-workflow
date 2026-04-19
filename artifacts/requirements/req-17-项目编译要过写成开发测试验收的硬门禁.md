# 项目编译要过写成开发测试验收的硬门禁

> req-id: req-17 | 完成时间: 2026-04-15 | 分支: main

## 需求目标

将项目基本编译/语法检查作为 `harness validate` 的默认检查项，确保代码在进入测试和验收前没有低级编译错误。

## 交付范围

**包含**：
- 扩展 `harness validate`，增加对 Python 项目的 `py_compile` 批量检查
- 在 `validate_requirement` 中集成编译检查并输出失败文件列表
- 文档更新

**不包含**：
- 多语言编译支持（本次仅 Python）
- 自动修复编译错误

## 验收标准

- [ ] `harness validate` 会遍历项目中所有 `.py` 文件并执行 `py_compile`
- [ ] 编译失败时列出具体文件和错误
- [ ] 文档已更新

## 变更列表

- **chg-01** validate 增加编译检查：在 `harness validate` 中加入 Python 语法编译检查，确保项目代码没有低级错误。
- **chg-02** 文档与验证：更新 README 文档，验证编译检查功能，并重新安装包。
