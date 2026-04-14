# chg-02 清理 CLI 产物目录

## 目标

删除 `context/rules/`（CLI 执行状态不属于知识层）。`versions/` 由 chg-07 在移除版本概念时一并删除，本变更不涉及。

## 背景

`context/rules/workflow-runtime.yaml` 在 `core.py` 中被标记为 `LEGACY_WORKFLOW_RUNTIME_PATH`，CLI 已优先使用 `state/runtime.yaml`。chg-07 完成后 CLI 将完全停止写入此文件，可安全删除整个目录。

## 范围

### 操作
- 删除 `.workflow/context/rules/`（含 `workflow-runtime.yaml`）

### 不修改
- `.workflow/versions/`（由 chg-07 负责）
- `state/runtime.yaml`
- 其他任何文件

## 验收标准

- [ ] `.workflow/context/rules/` 目录不再存在
- [ ] `context/` 下无 CLI 运行时状态文件
