# Requirement: 制品输出到分支特定目录

## Metadata

| Field | Value |
|-------|-------|
| **Requirement ID** | req-27 |
| **Title** | 制品输出到分支特定目录 |
| **Created** | 2026-04-19 |
| **Stage** | requirement_review |
| **Status** | draft |

## Background

当前制品输出到扁平目录结构 `artifacts/requirements/` 和 `artifacts/bugfixes/`。这在多分支开发环境中会造成问题：
- 不同分支的制品混在一起，难以区分来源
- 难以并行开发多个功能分支
- 难以进行分支级别的制品管理

用户明确要求制品按分支组织，例如：
- main 分支：`artifacts/main/requirements/`, `artifacts/main/bugfixes/`
- feature 分支：`artifacts/feature/requirements/`, `artifacts/feature/bugfixes/`

## Goal

修改 harness 命令，使其根据当前 git 分支自动将制品输出到 `artifacts/{branch}/` 目录下。

## Scope

### 需要修改的命令
- `harness requirement` - 需求制品输出到 `artifacts/{branch}/requirements/`
- `harness bugfix` - bugfix 制品输出到 `artifacts/{branch}/bugfixes/`
- `harness change` - change 制品输出到 `artifacts/{branch}/requirements/{req}/changes/`
- `harness archive` - 归档制品输出到 `artifacts/{branch}/archive/`

### 需要修改的文件
- `src/harness_workflow/workflow_helpers.py`
  - `create_requirement` 函数
  - `create_bugfix` 函数（刚修复的 bugfix-2 相关）
  - `create_change` 函数（刚修复的 bugfix-2 相关）
  - `generate_requirement_artifact` 函数

### 关键实现点
1. 获取当前 git 分支名：`git branch --show-current`
2. 动态构建路径：`artifacts/{branch_name}/...`
3. 确保 `artifacts/{branch}/` 目录存在

## Out of Scope
- 不修改已归档的制品位置（保持向后兼容）
- 不修改 `artifacts/` 根目录结构（现有 `artifacts/requirements/` 保持不变）

## Acceptance Criteria

| ID | 描述 | 验证方法 |
|----|------|----------|
| AC1 | `harness requirement <title>` 在 `artifacts/{branch}/requirements/` 下创建需求 | 运行命令后检查目录 |
| AC2 | `harness bugfix <title>` 在 `artifacts/{branch}/bugfixes/` 下创建 bugfix | 运行命令后检查目录 |
| AC3 | `harness change <title>` 在 `artifacts/{branch}/requirements/{req}/changes/` 下创建 change | 运行命令后检查目录 |
| AC4 | 分支名称正确获取（处理 main/master/feature 等） | 验证 git 分支解析 |
| AC5 | 现有 `artifacts/requirements/` 路径的制品不受影响 | 验证旧路径仍可访问 |

## 依赖关系

- **前置需求**: 无（但与 bugfix-2 相关 - bugfix-2 刚修复了扁平路径问题）

## 风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 分支名称含特殊字符 | 可能导致路径无效 | 对分支名进行 sanitize |
| 已有制品在新路径创建 | 旧分支制品可能被覆盖 | 告知用户需要手动迁移 |

## 待确认

1. 分支名称中的 `/` 或其他特殊字符如何处理？（例如 `feature/login` → `artifacts/feature_login/`？）
2. 已有制品是否需要迁移到新路径？
3. `artifacts/` 根目录是否保留作为默认/主分支入口？
