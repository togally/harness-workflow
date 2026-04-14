# chg-07 移除版本概念，需求成为顶层实体

## 目标

从 harness 系统彻底移除"版本"概念。顶层实体由 version 改为 requirement，归档操作直接针对需求进行，可指定目标文件夹（不存在则新建，存在则合并）。

## 背景

版本概念（`harness version`、`versions/active/` 目录、`meta.yaml`、`progress.yaml`）是旧架构的遗留，与新架构的需求中心设计高度重叠：
- `load_requirement_runtime()` / `save_requirement_runtime()` 已经是正确的需求中心实现
- `state/runtime.yaml` 已不含版本字段
- req-01 以来的实际使用完全走需求路径，版本路径从未真正激活

`.workflow/versions/` 中的数据（req-01 相关）无需迁移，直接删除。

## 范围

### 删除 core.py 中的版本相关函数（约 15 个）
- `create_version()`
- `set_active_version()`
- `use_version()`
- `rename_version()`（版本 rename 部分；需求/变更 rename 保留）
- `list_existing_versions()`
- `resolve_version_layout()`
- `require_active_version_id()`
- `current_version_layout()`
- `version_meta_path()`
- `load_version_meta()` / `save_version_meta()`
- `load_progress()` / `save_progress()`
- `sync_runtime_version()`
- `active_version_instruction()`
- `fallback_stage_for_artifacts()`
- `_print_progress_tree()`
- `_sync_artifact_statuses()`
- `_sync_progress()`
- `requirement_workflow_enabled()`（不再需要双模式判断，全面使用需求模式）

### 重写 archive_requirement()
新签名：`archive_requirement(root, requirement_name, folder="")`

行为：
- 从 `flow/requirements/req-xx-title/` 移动到 `flow/archive/<folder>/req-xx-title/`（指定 folder）
- 或移动到 `flow/archive/req-xx-title/`（不指定 folder）
- 目标文件夹不存在 → 新建
- 目标文件夹存在 → 直接写入（合并）
- 更新 `state/requirements/req-xx.yaml` 的 status 为 `archived`
- 更新 `state/runtime.yaml` 的 `active_requirements`（移除该 req）

### 删除 CLI 子命令
- `harness version` → 删除
- `harness active` → 删除
- `harness use` → 删除
- `harness plan` → 删除（plan.md 由 subagent 编排产出，用户不直接调用）
- `harness rename`（版本参数）→ 移除 `--version` 选项

### 更新 _required_dirs()
- 移除 `.workflow/versions` 和 `.workflow/versions/active` 的检查

### 删除版本相关常量和配置
- 删除 `Path(".workflow") / "versions"` 常量
- 停止写入 `LEGACY_WORKFLOW_RUNTIME_PATH`（`context/rules/workflow-runtime.yaml`）
- 删除 `DEFAULT_RUNTIME_CONFIG` 中的版本相关字段

### 删除命令文件
- `.claude/commands/harness-version.md`
- `.claude/commands/harness-active.md`
- `.claude/commands/harness-use.md`
- `.claude/commands/harness-plan.md`

### 更新命令文件
- `.claude/commands/harness-archive.md`：更新为 `harness archive <req-id> [--folder <name>]`
- `.claude/commands/harness-rename.md`：移除版本相关说明

### 删除 .workflow/versions/
- `rm -rf .workflow/versions/`（数据无需迁移，直接删除）

### 重装包
- `pip install -e .`

## 不修改
- `load_requirement_runtime()` / `save_requirement_runtime()`（保留，正确实现）
- `create_requirement()`, `rename_requirement()`, `rename_change()`（保留）
- `workflow_next()`, `workflow_status()` 等核心流程函数（保留，清理版本引用）
- `state/runtime.yaml` 的字段结构（已是需求中心，无需变动）

## 验收标准

- [ ] `core.py` 中无 `version_meta`、`load_version_meta`、`versions/active` 等版本相关符号
- [ ] `harness version`、`harness active`、`harness use` 命令已不存在
- [ ] `harness archive req-02 --folder v0.2` 正常执行，结果在 `flow/archive/v0.2/req-02-*/`
- [ ] `harness archive req-02`（不指定 folder）正常执行，结果在 `flow/archive/req-02-*/`
- [ ] 同一 folder 下归档第二个需求时正常合并（不报冲突）
- [ ] `.workflow/versions/` 不存在
- [ ] `harness status`、`harness next`、`harness requirement` 正常执行
- [ ] `pip install -e .` 后无 import 错误
