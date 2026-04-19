# Session Memory

## 1. Current Goal

实现 change 6：进度监控。在 `src/harness_workflow/core.py` 中新增 `progress.yaml` 读写、阶段自动更新、`harness status` 可视化进度树、以及 `harness next` 阶段门禁。

## 2. Current Status

已完成所有四个子任务：

1. **`load_progress` / `save_progress`**：新增于 `save_version_meta` 之后（约 2029 行）。使用 JSON 格式写入 `workflow/versions/active/<version_id>/progress.yaml`，支持嵌套结构。定义了 `DEFAULT_PROGRESS` 常量描述默认数据结构。

2. **`_sync_progress`**：新增于 `workflow_next` 之前（约 3463 行）。根据 `meta["stage"]` 推算各阶段 status，读取 changes 目录下 meta.yaml 统计 changes_total / changes_done，保存到 progress.yaml。

3. **`harness status` 进度树**：在 `workflow_status` 中 `approval_required` 输出之后，调用新增的 `_print_progress_tree`，按 需求/开发/测试/验收/完成 五个阶段输出带图标的进度行。

4. **`harness next` 阶段门禁**：在 `workflow_next` 中 `apply_stage_transition` 调用之前插入门禁逻辑：
   - `executing → testing`：`changes_done == changes_total`（且 total > 0）
   - `testing → acceptance`：`cases_failed == 0` 且 `bugs_open == 0`

已生成 `workflow/versions/active/v0.2.0-refactor/progress.yaml`，当前反映 `executing` 阶段实际状态（6 changes total, 0 done）。

## 3. Validated Approaches

- 用 JSON 格式存储 progress.yaml（文件名保持 .yaml，内容为 JSON），与项目已有的 `load_runtime`/`save_runtime` 风格一致，无需引入 PyYAML。
- 验证命令：
  ```bash
  python3 -c "import sys; sys.path.insert(0, 'src'); from harness_workflow.core import _sync_progress, workflow_status; print('OK')"
  ```
  输出：`OK`
- 端到端测试：`_sync_progress` 对 `testing` 阶段正确将 requirement/development 设为 done、testing 设为 in_progress；`_print_progress_tree` 输出格式正确。

## 4. Failed Paths

- 测试过程中对 v0.2.0-refactor 的 progress.yaml 产生了中间状态（testing 被设为 in_progress），已手动重置为与实际 `executing` 阶段一致的状态。

## 5. Candidate Lessons

```markdown
### 2026-04-11 progress.yaml 用 JSON 写入嵌套结构
- Symptom: 项目没有引入 PyYAML，但 progress 有嵌套字段，无法用现有 load_item_meta/save_item_meta 处理
- Cause: load_item_meta 只支持 key: value 扁平格式
- Fix: 采用 JSON 格式（文件名仍为 .yaml）与 load_runtime/save_runtime 保持风格一致，不引入新依赖
```

## 6. Next Steps

- 在 testing 阶段，由 subagent 或人工写入 progress.yaml 中的 cases_total / cases_passed / cases_failed / bugs_* 字段以触发门禁检查。
- 可考虑增加 `harness progress update --cases-total 10 --cases-passed 8` 等 CLI 命令便于手动更新测试计数。

## 7. Open Questions

- 无。
