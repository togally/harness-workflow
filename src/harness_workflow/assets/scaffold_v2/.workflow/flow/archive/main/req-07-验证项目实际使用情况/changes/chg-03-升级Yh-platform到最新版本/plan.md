# Plan: chg-03

## Steps

1. 确保 chg-02 已完成，harness update 命令已修复
2. 在 Yh-platform 目录下运行修复后的 `harness update`
3. 检查 update 结果：
   - `stages.md` 是否已更新为最新版
   - 角色文件是否已更新
   - 约束文件是否已更新
4. 手动检查并修复 `runtime.yaml`：
   - 添加 `ff_mode: false`
   - 添加 `ff_stage_history: []`
5. 手动检查并修复 `state/requirements/req-01-dockDetail新增字段.yaml`：
   - `req_id` → `id`
   - `created` → `created_at`
   - 添加 `started_at`、`completed_at`、`stage_timestamps`
6. 检查并创建 `state/sessions/req-01/` 目录
7. 验证核心文件一致性

## Artifacts

- 更新后的 Yh-platform `.workflow/` 目录

## Dependencies

- 依赖 chg-02 修复的 install/update 机制
