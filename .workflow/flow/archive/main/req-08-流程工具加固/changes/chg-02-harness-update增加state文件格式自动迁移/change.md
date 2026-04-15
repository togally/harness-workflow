# Change: chg-02

## Title

harness update 增加 state 文件格式自动迁移

## Goal

让 `harness update` 在更新 managed 文档后，自动检测并迁移旧版 `runtime.yaml` 和 `requirements/*.yaml` 的字段格式到新规范。

## Scope

**包含**：
- 在 `core.py` 的 `update_repo` 流程中增加 state 格式检测和迁移
- 支持 `runtime.yaml`：添加缺失的 `ff_mode`、`ff_stage_history`
- 支持 `requirements/*.yaml`：`req_id`→`id`、`created`→`created_at`、`completed`→`completed_at`，添加 `started_at`、`stage_timestamps`
- 迁移前备份旧文件
- 输出迁移报告

**不包含**：
- 修改非 `.workflow/state/` 下的其他 yaml
- 自动推断缺失的 `stage_timestamps` 精确时间（使用 `created_at` 降级填充）

## Acceptance Criteria

- [ ] `harness update` 能检测旧版 `runtime.yaml` 并自动升级
- [ ] `harness update` 能检测旧版 `requirements/*.yaml` 并自动升级
- [ ] 迁移前会备份旧文件
- [ ] 升级后的文件能被当前 workflow 正常解析
