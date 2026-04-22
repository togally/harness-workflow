# Change

## 1. Title

扩展 harness migrate 子命令迁移 legacy archive 到 primary

## 2. Goal

- 新增 `harness migrate archive` 子命令（与现有 `harness migrate requirements` 对称），把 `.workflow/flow/archive/` 下已有归档批量迁移到 `artifacts/{branch}/archive/`，默认 dry-run、幂等、可回滚。

## 3. Requirement

- `req-29`

## 4. Scope

### Included

- 扩展 `src/harness_workflow/tools/harness_migrate.py`：`resource` choices 增加 `"archive"`；接入新 helper `migrate_archive(root, dry_run)`。
- 在 `src/harness_workflow/workflow_helpers.py` 新增 `migrate_archive` helper：遍历 `.workflow/flow/archive/` 下所有子条目（含 `main/...`、历史分支、`req-20-...`、各 `bugfix-N` 等），逐条复制到 `artifacts/{branch}/archive/<同层结构>`，成功后再删 legacy 对应条目。
- 实现幂等：目标路径已存在且内容一致时跳过；内容不一致时停下、打印冲突列表、返回非零，**不自动覆盖**。
- dry-run 策略与 `harness migrate requirements` 对齐：传 `--dry-run` 时仅打印计划、退出码 0、不动文件；不传则真实执行。
- 新增 `tests/test_migrate_archive.py`：覆盖 happy path（迁移成功 + legacy 清空）、幂等重跑、multi-branch 子树、冲突场景。

### Excluded

- 不修改 `resolve_archive_root` 判据（由 chg-01 负责）。
- 不清理 `.workflow/flow/archive/` 的父目录（保留空目录 + `.gitkeep`，避免误删）。
- 不迁移 `.workflow/flow/requirements/` 等其他 legacy 目录（`harness migrate requirements` 已有）。
- 不做跨仓库迁移。

## 5. Acceptance

- Covers requirement.md **AC-04**：`harness migrate archive` 能把 legacy 已有归档（req-26 / req-27 / req-28 / bugfix-3 / bugfix-4 / bugfix-5 / bugfix-6 等）迁到 primary；迁移后再跑 `harness status` / `harness archive`，不再出现 `using legacy archive path` 警告。
- 幂等：重复执行命令 → 无变化，退出码 0，打印 `already migrated`。
- 冲突检测：legacy 与 primary 同名目录内容不一致时 → 打印冲突路径、退出码非零，不动文件。

## 6. Risks

- **R1 不可逆**：迁移涉及物理移动，失败可能留下"两边都有"或"两边都没有"的脏状态 → 实施策略：**copy-then-verify-then-unlink**（先 copy、比对文件列表/hash、再删 legacy 侧），任意步骤失败直接 abort 保持 legacy 完整。
- **R2 分支命名**：legacy 下历史有 `req-20-...`（旧扁平结构）和 `main/...`（分支结构）两种形态，迁移需对每种形态分别归档：旧扁平 → `artifacts/main/archive/<原目录>`，分支结构 → `artifacts/<branch>/archive/<原目录>`。
- **R3 依赖顺序**：本 change 依赖 chg-01 的"primary 优先"判据，否则 `harness status` 迁移后仍可能误报 → 实施时同 PR 内先合 chg-01。
