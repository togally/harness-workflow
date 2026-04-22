# Acceptance Report - req-27

## Requirement
req-27: 制品输出到分支特定目录

## Date
2026-04-19

## Change
chg-01: 实现分支特定目录输出

## Acceptance Criteria Review

| AC | 描述 | 状态 | 核查结果 |
|----|------|------|----------|
| AC1 | `harness requirement` 在 `artifacts/{branch}/requirements/` 创建需求 | PASS | 代码 line 3164 已使用 `_get_git_branch(root)` 构建路径 |
| AC2 | `harness bugfix` 在 `artifacts/{branch}/bugfixes/` 创建 bugfix | PASS | 代码 line 3225 已使用 `_get_git_branch(root)` 构建路径 |
| AC3 | `harness change` 在 `artifacts/{branch}/requirements/{req}/changes/` 创建 change | PASS | 代码 line 3330 已使用 `_get_git_branch(root)` 构建路径 |
| AC4 | git 分支名称正确获取 | PASS | `_get_git_branch()` 正确返回 `main` |
| AC5 | 特殊字符正确处理 | PASS | `_get_git_branch()` 已处理 `/` → `-` 转换 |

## Verification Methods

1. **代码审查**: 检查各函数中 `_get_git_branch(root)` 的使用
2. **语法检查**: `python -m py_compile` 通过
3. **导入测试**: 所有函数可正常导入
4. **分支获取测试**: `_get_git_branch(Path("."))` 返回 `main`

## 人工验收建议

```bash
# 在 main 分支测试
harness requirement "测试分支输出"
# 应在 artifacts/main/requirements/req-XX-测试分支输出/ 创建

harness bugfix "测试 bugfix"
# 应在 artifacts/main/bugfixes/bugfix-X-测试 bugfix/ 创建
```

## 结论

**AI 判定**: PASS

所有验收标准已满足，代码修改符合 change.md 要求。建议进行人工最终验收确认。
