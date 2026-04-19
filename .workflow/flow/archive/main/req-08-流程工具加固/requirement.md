# Requirement

## 1. Title

流程工具加固

## 2. Goal

req-07 在 Yh-platform 项目验证中发现了三个高频痛点：
1. `harness install` 部署的模板容易与仓库最新状态脱节（scaffold_v2 未同步）
2. `harness update` 只更新 managed 文档，不处理旧版 `state/` 文件格式的迁移
3. `harness archive` 归档后未清理 `flow/requirements/` 中的残留目录

这些问题都指向 **Harness workflow 的 CLI 工具在自动化和鲁棒性上的不足**。本需求的目标是：**通过 lint 检查、自动迁移、归档清理三种手段，提升工具的自动化程度和用户的零维护体验**。

## 3. Scope

**包含**：
- 在 `lint_harness_repo.py` 或 CI 脚本中增加 scaffold_v2 同步检查
- 在 `harness update` 中增加旧版 `runtime.yaml` / `requirements/*.yaml` 的格式自动迁移
- 在 `harness archive` 中增加归档后自动清理 `flow/requirements/` 残留目录的逻辑
- 更新相关文档和测试

**不包含**：
- 修改 workflow 的核心阶段定义或角色职责
- 开发全新的监控 Dashboard
- 修改业务项目的业务代码

## 4. Acceptance Criteria

- [ ] `lint_harness_repo.py` 能够检测 `src/harness_workflow/assets/scaffold_v2/` 是否与仓库 `.workflow/` 同步
- [ ] `harness update` 在检测到旧版 `state/` 文件时，能够自动升级字段格式（或至少给出明确的升级提示和操作指引）
- [ ] `harness archive` 执行后，`flow/requirements/` 中对应需求目录已被清理
- [ ] 至少在一个测试项目（如 Yh-platform 或临时目录）中验证了上述三项功能

## 5. Split Rules

### chg-01 lint 增加 scaffold_v2 同步检查

修改 `lint_harness_repo.py`（或在 harness-workflow 仓库 CI 中新增检查脚本）：
- 计算 `.workflow/flow/stages.md` 与 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md` 的哈希或内容差异
- 如果不一致，返回错误并提示 "scaffold_v2 未同步，请执行 cp -R .workflow ..."
- 可选：检查其他关键文件（如 `WORKFLOW.md`、`CLAUDE.md`、核心角色文件）

### chg-02 harness update 增加 state 文件格式自动迁移

修改 `core.py` 中的 `update_repo` 或相关逻辑：
- 在更新 managed 文件后，检查 `runtime.yaml` 是否包含 `ff_mode`、`ff_stage_history`
- 检查 `state/requirements/*.yaml` 是否使用旧字段（`req_id`、`created`、`completed`）
- 如检测到旧格式，自动改写为新格式并备份旧文件
- 输出迁移报告

### chg-03 harness archive 自动清理残留目录

修改 `core.py` 中的归档逻辑：
- 在需求成功移动到 `flow/archive/` 后，自动删除 `flow/requirements/{req-id}/`（如果仍存在）
- 记录清理动作到日志

### chg-04 验证与文档更新

- 在 harness-workflow 仓库的测试脚本中增加对上述三项的测试
- 更新 `stages.md` 或 CLI 文档中关于 `update` 和 `archive` 的说明
- 用 Yh-platform 或临时项目做 live 验证
