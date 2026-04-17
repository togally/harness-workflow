# Plan: chg-05 重构经验文件目录与加载规则

## 执行顺序

### Step 1: 移动并重命名经验文件
- 创建目录 `.workflow/context/experience/roles/`
- 执行以下移动/重命名：
  - `context/experience/stage/requirement.md` → `context/experience/roles/requirement-review.md`
  - `context/experience/stage/planning.md` → `context/experience/roles/planning.md`
  - `context/experience/stage/development.md` → `context/experience/roles/executing.md`
  - `context/experience/stage/testing.md` → `context/experience/roles/testing.md`
  - `context/experience/stage/acceptance.md` → `context/experience/roles/acceptance.md`
  - `context/experience/stage/regression.md` → `context/experience/roles/regression.md`
- 删除空目录 `context/experience/stage/`
- 产物：新的 `experience/roles/` 目录结构

### Step 2: 更新 experience/index.md
- 将 `stage/` 的引用全部替换为 `roles/`
- 更新文件列表：
  - `roles/acceptance.md`
  - `roles/executing.md`
  - `roles/planning.md`
  - `roles/regression.md`
  - `roles/requirement-review.md`
  - `roles/testing.md`
- 保留 `risk/` 和 `tool/` 的引用不变
- 产物：更新后的 `experience/index.md`

### Step 3: 更新 stage-role.md 中的经验加载规则
- 将规则中的 `experience/stage/` 路径更新为 `experience/roles/`
- 将按 stage 映射更新为按角色名直接匹配：
  | 角色名 | 对应经验文件 |
  |--------|-------------|
  | requirement-review | `experience/roles/requirement-review.md` |
  | planning | `experience/roles/planning.md` |
  | executing | `experience/roles/executing.md` |
  | testing | `experience/roles/testing.md` |
  | acceptance | `experience/roles/acceptance.md` |
  | regression | `experience/roles/regression.md` |
  | done | 不强制加载特定经验文件，但可加载同阶段相关经验 |
- 产物：更新后的 `stage-role.md`

### Step 4: 扫描并更新所有 stage 角色文件
- 使用 grep 搜索 `experience/stage/` 在所有 stage 角色文件中的引用
- 对 requirement-review.md、planning.md、executing.md、testing.md、acceptance.md、regression.md、done.md、tools-manager.md 逐一检查
- 将所有 `experience/stage/` 引用替换为 `experience/roles/`，并按需要更新文件名映射
- 产物：无残留引用的 stage 角色文件

### Step 5: 扫描 technical-director.md 和 done.md
- 检查 `technical-director.md` 中是否直接引用 `experience/stage/`
- 检查 `done.md` 中"经验沉淀验证"步骤是否引用旧路径
- 如有残留，更新为 `experience/roles/`
- 产物：无残留引用的 Director 和 done 文件

### Step 6: 验证目录结构和引用完整性
- 确认 `context/experience/stage/` 已不存在
- 确认 `context/experience/roles/` 下包含 6 个文件
- 使用 grep 全局搜索 `experience/stage/`，确认无任何残留引用
- 产物：验证通过标记

## 依赖关系

- **前置依赖**：chg-04 必须已完成（因为需要 `stage-role.md` 存在以更新其经验加载规则）
- **后续影响**：无（chg-05 是纯文件迁移和引用更新，不影响其他变更）
