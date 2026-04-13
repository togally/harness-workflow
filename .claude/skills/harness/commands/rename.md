# harness rename requirement|change "<old>" "<new>"

## 前置条件
- 目标需求或变更存在

## 执行步骤（rename requirement）
1. 重命名目录：`flow/requirements/{old}` → `flow/requirements/{new}`
2. 更新 `state/requirements/{old}.yaml` → 文件重命名为 `{new}.yaml`，内部 id/title 字段同步更新
3. 更新 `state/runtime.yaml` 中对该需求的所有引用
4. 更新 `state/sessions/` 中对应目录名

## 执行步骤（rename change）
1. 重命名目录：`flow/requirements/{req-id}/changes/{old}` → `…/{new}`
2. 更新 `state/requirements/{req-id}.yaml` 的 `change_ids` 列表

## 错误处理
- 目标名称已存在 → 提示冲突，不执行重命名
