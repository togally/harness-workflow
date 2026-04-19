# Change: chg-01

## Title
validate 增加编译检查

## Goal
在 `harness validate` 中加入 Python 语法编译检查，确保项目代码没有低级错误。

## Scope

**包含**：
- 修改 `core.py` 的 `validate_requirement`
- 遍历项目中所有 `.py` 文件
- 使用 `py_compile.compile` 检查语法
- 打印失败文件及错误信息

**不包含**：
- 非 Python 语言支持
- 自动修复

## Acceptance Criteria

- [ ] `harness validate` 执行编译检查
- [ ] 语法错误时输出具体文件和异常信息
- [ ] 全部通过时无编译相关报错
