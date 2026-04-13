# harness archive "<req-id>" [--version "<v>"]

## 前置条件
- 指定需求的 stage 是 `done`

## 执行步骤
1. 确定归档路径：
   - 有 --version：`workflow/flow/archive/{v}/`
   - 无 --version：`workflow/flow/archive/`
2. 创建目标目录（如不存在）
3. 移动 `workflow/flow/requirements/{req-id}/` → 归档路径
4. 更新 `state/requirements/{req-id}.yaml`：stage 改为 `archived`
5. 从 `state/runtime.yaml` 的 `active_requirements` 移除该 req-id
6. `state/sessions/{req-id}/` 保留不删

## 错误处理
- 需求 stage 不是 done → 提示需先完成验收
- 归档路径已有同名目录 → 提示确认是否覆盖或重命名
