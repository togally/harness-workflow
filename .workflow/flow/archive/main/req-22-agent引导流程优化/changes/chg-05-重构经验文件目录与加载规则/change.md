# chg-05: 重构经验文件目录与加载规则

## 目标

将经验文件从按 stage 划分改为按角色划分，使经验加载的粒度与角色粒度对齐，消除同一 stage 内不同角色经验污染或遗漏的问题。

## 范围

### 包含

- 重构 `.workflow/context/experience/` 目录结构：
  - 将 `stage/` 重命名为 `roles/`
  - 将 `stage/requirement.md` 重命名为 `roles/requirement-review.md`
  - 将 `stage/planning.md` 保留（与角色同名）
  - 将 `stage/development.md` 重命名为 `roles/executing.md`
  - 将 `stage/testing.md` 保留（与角色同名）
  - 将 `stage/acceptance.md` 保留（与角色同名）
  - 将 `stage/regression.md` 保留（与角色同名）
  - `tool/` 和 `risk/` 目录保持不变
- 更新 `.workflow/context/experience/index.md`：
  - 将 `stage/` 的引用更新为 `roles/`
  - 更新文件列表和描述
- 更新 `.workflow/context/roles/stage-role.md`（chg-04 新建）：
  - 将经验加载规则中的 `stage/` 路径更新为 `roles/`
  - 将按 stage 映射更新为按角色名直接匹配（如 `requirement-review.md`、`planning.md` 等）
- 检查并更新所有 stage 角色文件（requirement-review.md ~ done.md）中直接引用 `experience/stage/` 的路径
- 检查 `technical-director.md` 和 `done.md` 中是否有直接引用 `experience/stage/` 的内容，如有则更新

### 不包含

- 不修改经验文件的实际内容（仅移动和重命名）
- 不修改 `base-role.md`（由 chg-04 负责）
- 不修改 `role-loading-protocol.md`（由 chg-04 负责）
- 不新建或删除任何经验条目

## 验收标准

- [ ] `context/experience/stage/` 目录已不存在，文件已迁移到 `context/experience/roles/`
- [ ] `context/experience/index.md` 正确列出 `roles/` 下的所有文件
- [ ] `stage-role.md` 中的经验加载规则引用的是 `experience/roles/` 路径
- [ ] 所有 stage 角色文件中无残留的 `experience/stage/` 路径引用
- [ ] `technical-director.md` 和 `done.md` 中无残留的 `experience/stage/` 路径引用
