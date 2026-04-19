# Validation Report: req-07 验证项目实际使用情况

## 执行摘要

以 `/Users/jiazhiwei/IdeaProjects/Yh-platform` 为验证对象，全面审计并修复了 Harness workflow 在实际项目中的部署问题。

## 发现的问题

### 问题 1：`harness install` 部署的模板严重过时
**现象**：Yh-platform 中的 `stages.md`、角色文件、约束文件均为旧版本，缺少 req-05（ff 模式）和 req-06（时长记录）的所有改进。

**根因**：`harness_workflow` 包内 `src/harness_workflow/assets/scaffold_v2/` 中的模板文件未被同步更新。`install_repo` → `_sync_requirement_workflow_managed_files` 始终从该目录读取文件，导致所有新安装/更新的项目都拿到旧模板。

### 问题 2：`state/` 文件结构不兼容
**现象**：`runtime.yaml` 缺少 `ff_mode`、`ff_stage_history`；`requirements/*.yaml` 使用旧字段名。

**根因**：`harness update` 只同步 managed 文件（`.workflow/` 下的文档），不修改 `runtime.yaml` 和 `requirements/*.yaml`。这些文件在项目初始化后由工作流动态生成，update 命令没有设计状态格式迁移逻辑。

### 问题 3：session-memory 完全缺失
**现象**：`state/sessions/` 目录为空，req-01 执行过程中未保存各 stage 的 session-memory。

**根因**：旧版本模板中 `state/sessions/` 只有空目录，且执行过程中 agent 未按规范保存 session-memory（旧模板的角色文件中对此要求不够明确）。

### 问题 4：归档产物不完整
**现象**：archive 中 req-01 缺少 `done-report.md`，testing 产物命名为 `test-results.md`，`flow/requirements/` 下残留 req-01 目录。

**根因**：旧版本工作流对 done 阶段和归档阶段的产物要求不完整，且归档后未清理 `flow/requirements/` 中的残留。

## 修复动作

1. **同步 scaffold 模板**：将 harness-workflow 仓库最新的 `.workflow/`、`WORKFLOW.md`、`CLAUDE.md` 复制到 `src/harness_workflow/assets/scaffold_v2/`
2. **重新安装包**：`pipx inject harness-workflow . --force`
3. **验证 install**：在临时目录验证 `harness install` 已能部署最新模板
4. **升级 Yh-platform**：运行 `harness update` 同步所有 managed 文件
5. **手动修复 state**：更新 `runtime.yaml` 和 `requirements/*.yaml` 到新结构
6. **补全 req-01 产物**：在 `state/sessions/req-01/` 下补全 session-memory、testing-report、acceptance-report、done-report
7. **清理残留**：删除 `flow/requirements/` 中残留的 req-01 目录

## 改进建议

> **建议 1**：在 CI 或 lint 脚本中增加 scaffold 同步检查。例如对比 `.workflow/flow/stages.md` 和 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md` 的哈希值，不一致时报警。

> **建议 2**：`harness update` 应增加状态格式迁移逻辑。当检测到 `runtime.yaml` 或 `requirements/*.yaml` 使用旧字段时，提示用户或自动升级。

> **建议 3**：在 `done.md` 或 `WORKFLOW.md` 中强化 session-memory 保存要求，并在各角色文件的"上下文维护职责"中增加更明确的检查点。

> **建议 4**：`harness archive` 命令应自动清理 `flow/requirements/` 中的残留目录，避免归档后活跃需求和归档副本并存。
