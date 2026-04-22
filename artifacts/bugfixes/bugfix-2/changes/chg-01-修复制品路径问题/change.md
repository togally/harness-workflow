# Change: 修复制品路径问题

## ID
chg-01

## Title
修复制品路径问题

## Requirement
bugfix-2

## Goal
修复 `create_bugfix` 和 `create_change` 函数的制品输出路径，使其输出到 `artifacts/` 目录而非 `.workflow/flow/`。

## Background
诊断发现 `harness bugfix` 和 `harness change` 命令的制品输出路径与用户要求不一致：
- 用户要求所有制品输出到 `artifacts/` 目录
- 当前代码输出到 `.workflow/flow/` 目录

## Scope

### 需要修改的文件
- `src/harness_workflow/workflow_helpers.py`

### 需要修改的函数
1. `create_bugfix` (line ~3222)
   - 当前: `root / ".workflow" / "flow" / "bugfixes" / dir_name`
   - 修改为: `root / "artifacts" / "bugfixes" / dir_name`

2. `create_change` (line ~3326)
   - 当前: `root / ".workflow" / "flow" / "requirements"`
   - 修改为: `root / "artifacts" / "requirements"`

3. `create_change` (line ~3333)
   - 当前: `req_dir / "changes" / dir_name`
   - 修改为: 保持相对路径结构，但 req_dir 指向 `artifacts/requirements/`

## Out of Scope
- 不修改其他函数或文件
- 不修改 `create_requirement` 函数（需求创建）
- 不修改归档相关函数

## Acceptance Criteria
- [ ] `create_bugfix` 在 `artifacts/bugfixes/` 创建 bugfix 工作区
- [ ] `create_change` 在 `artifacts/requirements/` 查找需求
- [ ] `create_change` 在 `artifacts/requirements/<req>/changes/` 创建变更工作区
- [ ] 新创建的 bugfix 和 change 制品结构正确
