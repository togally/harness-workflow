# Change: chg-03

## Title

升级 Yh-platform 的 workflow 到最新版本

## Goal

将 Yh-platform 项目的 Harness workflow 升级到最新规范，确保核心文档和状态结构与 harness-workflow 仓库一致。

## Scope

**包含**：
- 在 Yh-platform 中运行修复后的 `harness update`（或手动同步核心文件）
- 更新 `runtime.yaml` 和 `state/requirements/*.yaml` 到新结构
- 同步 `stages.md`、角色文件、约束文件到最新版本
- 确保 `state/sessions/` 目录结构符合新规范

**不包含**：
- 修改 Yh-platform 业务代码
- 补全 req-01 的具体产物（属于 chg-04）

## Acceptance Criteria

- [ ] Yh-platform 的 `stages.md`、角色文件、约束文件与 harness-workflow 最新状态一致
- [ ] `runtime.yaml` 已更新为新结构
- [ ] `state/requirements/*.yaml` 已更新为新字段规范
