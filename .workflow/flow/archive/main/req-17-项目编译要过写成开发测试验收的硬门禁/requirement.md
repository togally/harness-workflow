# Requirement

## 1. Title

项目编译要过写成开发测试验收的硬门禁

## 2. Goal

将项目基本编译/语法检查作为 `harness validate` 的默认检查项，确保代码在进入测试和验收前没有低级编译错误。

## 3. Scope

**包含**：
- 扩展 `harness validate`，增加对 Python 项目的 `py_compile` 批量检查
- 在 `validate_requirement` 中集成编译检查并输出失败文件列表
- 文档更新

**不包含**：
- 多语言编译支持（本次仅 Python）
- 自动修复编译错误

## 4. Acceptance Criteria

- [ ] `harness validate` 会遍历项目中所有 `.py` 文件并执行 `py_compile`
- [ ] 编译失败时列出具体文件和错误
- [ ] 文档已更新

## 5. Split Rules

### chg-01 validate 增加编译检查
- 修改 `core.py` 的 `validate_requirement`
- 遍历 `src/**/*.py`（或项目根目录下所有 `.py`）
- 调用 `py_compile.compile` 检查语法
- 汇总失败项并打印

### chg-02 文档与验证
- 更新 README 说明 `harness validate` 包含编译检查
- 本地制造一个语法错误验证检测能力
- pipx inject 重新安装
