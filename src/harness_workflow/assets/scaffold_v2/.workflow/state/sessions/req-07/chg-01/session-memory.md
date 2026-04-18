# Session Memory: chg-01

## Change
Yh-platform 项目 Harness workflow 差距审计

## Status
✅ 已完成

## Steps
- [x] 读取 Yh-platform 的 `stages.md`、角色文件、约束文件
- [x] 读取 harness-workflow 最新对应文件
- [x] 逐文件对比差异
- [x] 检查 `harness_workflow` 包中 scaffold 模板来源
- [x] 产出审计报告

## Audit Report

### 根因结论
`harness install` / `harness update` 安装旧版本的根本原因是：
**`src/harness_workflow/assets/scaffold_v2/` 中的模板文件未被同步更新为 harness-workflow 仓库的最新版本。**

`install_repo` → `init_repo` → `_sync_requirement_workflow_managed_files` → `_managed_file_contents` → `_scaffold_v2_file_contents` 的调用链始终从包内 `assets/scaffold_v2/` 读取文件。当仓库的 `.workflow/` 被更新（如 req-05、req-06 的改动）时，开发者没有同步更新 `src/harness_workflow/assets/scaffold_v2/`，导致所有新安装/更新的项目都拿到旧模板。

### 详细差距清单

#### 1. `stages.md`
**Yh-platform 状态**：旧版，100 行，无 ff 模式、无时长记录
**最新规范**：~185 行，包含：
- harness ff（fast-forward）完整章节
- 自动推进规则、AI 决策边界、失败处理路径
- ff 模式下 session-memory 规范
- 暂停与退出机制
- 需求实现时长记录章节

#### 2. 角色文件
**Yh-platform 状态**：所有角色文件均为初始模板，无 ff 相关说明
**缺失内容**：
- `planning.md`：缺少 ff 模式下自动推进说明
- `executing.md`：缺少 ff 说明
- `testing.md`：缺少 ff 说明
- `acceptance.md`：缺少 ff 说明
- `requirement-review.md`：缺少 ff 说明
- `regression.md`：缺少 ff 说明
- `done.md`：缺少 done-report.md 头部的"实现时长"模板

#### 3. 约束文件
**Yh-platform 状态**：
- `boundaries.md`：只有基础边界，无 ff 决策边界
- `recovery.md`：只有失败三条路径和上下文交接，无"平台级错误恢复"和"skill 缺失处理"

#### 4. `state/` 结构
**Yh-platform 状态**：
- `runtime.yaml`：缺少 `ff_mode`、`ff_stage_history`
- `requirements/req-01-dockDetail新增字段.yaml`：使用旧字段 `req_id`、`created`、`completed`，缺少 `started_at`、`stage_timestamps`、`archived_at`
- `state/sessions/`：完全为空，没有任何 session-memory

#### 5. `flow/` 结构
**Yh-platform 状态**：
- archive 中 req-01 缺少 `done-report.md`
- archive 中 testing 产物命名为 `test-results.md`（旧命名）
- `flow/requirements/` 下仍残留 req-01 目录（归档后未清理）
- session-memory 散落在 `changes/` 目录下（旧规范），未集中到 `state/sessions/`

#### 6. 经验文件
**Yh-platform 状态**：`context/experience/tool/` 下只有 `harness.md`
**缺失**：`harness-ff.md`、`claude-code-context.md`

### 影响评估
- **高影响**：所有通过 `harness install` 新部署的项目都会拿到过时模板，无法使用 req-05 ~ req-06 的新功能
- **中影响**：已部署项目通过 `harness update` 也无法获得新模板，因为 update 同样读取旧 scaffold
- **低影响**：harness-workflow 仓库自身通过自举验证不受影响，但外部用户会一致遇到版本落后问题

## Notes
根因已明确为 scaffold_v2 模板未同步。下一步直接修复模板同步机制。
