# Session Memory - bugfix-2

## 状态
**完成** - 2026-04-19

## 概述
bugfix-2 成功修复了 `harness bugfix` 和 `harness change` 命令的制品输出路径问题。

## 修复内容

### 代码修改
**文件**: `src/harness_workflow/workflow_helpers.py`

| 位置 | 函数 | 修改 |
|------|------|------|
| Line 3222 | `create_bugfix` | `.workflow/flow/bugfixes/` → `artifacts/bugfixes/` |
| Line 2867 | `_next_bugfix_id` | 添加 `artifacts/bugfixes/` 到扫描路径 |
| Line 3326 | `create_change` | `.workflow/flow/requirements/` → `artifacts/requirements/` |

## 验收结果
- [x] AC1: `create_bugfix` 使用 `artifacts/bugfixes/`
- [x] AC2: `create_change` 在 `artifacts/requirements/` 查找需求
- [x] AC3: `create_change` 输出路径正确
- [x] AC4: `_next_bugfix_id` 扫描 `artifacts/bugfixes/`

**人工判定**: 通过

## 经验沉淀

### 问题
`harness bugfix` 和 `harness change` 命令的制品输出路径与用户要求不一致

### 根因
代码硬编码了 `.workflow/flow/` 路径

### 解决方案
将输出路径统一修改为 `artifacts/` 目录

### 教训
- 用户明确要求所有制品输出到 `artifacts/` 目录
- 代码中的路径硬编码需要统一管理，避免不一致
- `resolve_requirement_reference` 等辅助函数也需要同步更新

## 下一步
无 - bugfix-2 完成
