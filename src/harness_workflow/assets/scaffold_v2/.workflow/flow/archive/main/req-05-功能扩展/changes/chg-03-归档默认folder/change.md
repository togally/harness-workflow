# Change

## 1. Title
归档默认 folder = 当前 git 分支名

## 2. Goal
当 `harness archive` 不传 `--folder` 参数时，自动读取当前 git 分支名作为默认 folder，使归档目录自动组织到与开发分支同名的子目录下，便于按分支追溯需求历史。非 git 仓库或 branch 读取失败时降级为原有行为（直接放 `archive/` 下）。

## 3. Requirement
- req-05-功能扩展

## 4. Scope
**包含**：
- `src/harness_workflow/core.py`：`archive_requirement()` 函数增加 git branch 读取逻辑
- branch 名中 `/` 替换为 `-`（如 `feature/auth` → `feature-auth`）
- 非 git 仓库（`git branch --show-current` 失败或返回空）时降级为 `folder=""`（原有行为）

**不包含**：
- CLI 参数定义变更（`--folder` 仍保留，显式传入时优先使用）
- `workflow_archive` 的其他逻辑改动
- 交互式选择相关改动（属于 chg-04）

## 5. Acceptance Criteria
- [ ] `harness archive req-xx`（不传 `--folder`）在 `main` 分支时，归档到 `.workflow/flow/archive/main/req-xx-{title}/`
- [ ] `harness archive req-xx --folder custom` 显式传入时，使用 `custom` 作为 folder（不读取 branch）
- [ ] branch 名含 `/`（如 `feature/auth`）时自动替换为 `-`，归档到 `feature-auth/` 下
- [ ] 非 git 仓库时降级，直接放 `.workflow/flow/archive/req-xx-{title}/` 下（与现有行为一致）
- [ ] `git branch --show-current` 返回空字符串时同样降级

## 6. Dependencies
- **前置**：无（独立变更）
- **后置**：chg-04（交互式选择改造 archive_requirement，需要在 chg-03 基础上叠加）
