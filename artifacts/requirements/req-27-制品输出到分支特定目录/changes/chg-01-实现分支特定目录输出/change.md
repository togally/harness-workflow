# Change: 实现分支特定目录输出

## ID
chg-01

## Title
实现分支特定目录输出

## Requirement
req-27

## Goal
修改 harness 命令使其根据当前 git 分支将制品输出到 `artifacts/{branch}/` 目录。

## Scope

### 需要修改的函数
1. `create_requirement` - 输出到 `artifacts/{branch}/requirements/`
2. `create_bugfix` - 输出到 `artifacts/{branch}/bugfixes/`
3. `create_change` - 输出到 `artifacts/{branch}/requirements/{req}/changes/`
4. `generate_requirement_artifact` - 输出到 `artifacts/{branch}/requirements/`

### 关键实现
1. 创建辅助函数 `_get_branch_name(root: Path) -> str`
   - 执行 `git branch --show-current`
   - 处理无分支情况（返回 "main" 作为默认值）

2. 修改所有输出路径前缀
   - 从: `root / "artifacts" / "requirements"`
   - 改为: `root / "artifacts" / _get_branch_name(root) / "requirements"`

3. 分支名 sanitization
   - 将 `/` 替换为 `-`（例如 `feature/login` → `feature-login`）
   - 去除空白字符

## Out of Scope
- 不迁移现有制品到新路径
- 不修改归档路径（保持向后兼容）

## Acceptance Criteria
- [ ] `harness requirement` 在正确分支目录创建需求
- [ ] `harness bugfix` 在正确分支目录创建 bugfix
- [ ] `harness change` 在正确分支目录创建 change
- [ ] git 分支名称正确获取
- [ ] 特殊字符正确处理
