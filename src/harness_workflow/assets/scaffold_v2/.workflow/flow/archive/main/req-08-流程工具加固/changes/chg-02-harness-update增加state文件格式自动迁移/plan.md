# Plan: chg-02

## Steps

1. 读取 `core.py` 中 `update_repo` 和相关函数的实现
2. 设计 `_migrate_runtime_yaml(root)` 函数：
   - 读取 `runtime.yaml`
   - 检查是否缺少 `ff_mode`、`ff_stage_history`
   - 如有缺失，备份旧文件为 `runtime.yaml.bak`
   - 添加缺失字段并保存
3. 设计 `_migrate_requirement_yaml(root, yaml_path)` 函数：
   - 读取 `state/requirements/*.yaml`
   - 检查旧字段：`req_id`→`id`、`created`→`created_at`、`completed`→`completed_at`
   - 添加 `started_at`（如缺失用 `created_at` 填充）、`stage_timestamps`（空对象）、`completed_at`（如 done/archived 且缺失用当前时间或占位）
   - 备份旧文件并保存新内容
4. 在 `update_repo` 流程末尾调用迁移函数（仅在非 check 模式下）
5. 输出迁移动作到 `actions` 列表
6. 在 Yh-platform 或临时项目中测试：
   - 准备旧格式 yaml
   - 运行 `harness update`
   - 验证字段已升级

## Artifacts

- 更新后的 `core.py`

## Dependencies

- 无
