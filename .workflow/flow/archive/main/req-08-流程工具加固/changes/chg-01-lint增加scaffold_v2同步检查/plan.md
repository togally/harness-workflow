# Plan: chg-01

## Steps

1. 读取当前 `lint_harness_repo.py`，理解现有检查逻辑
2. 新增 `_check_scaffold_v2_sync()` 函数：
   - 定位仓库根目录 `.workflow/flow/stages.md`
   - 定位 `src/harness_workflow/assets/scaffold_v2/.workflow/flow/stages.md`
   - 比较两者内容（直接全文对比或哈希对比）
   - 不一致时记录错误信息
3. 可选：增加 `WORKFLOW.md` 和 `CLAUDE.md` 的同步检查
4. 在主 lint 流程中调用新检查函数
5. 本地运行 `python3 lint_harness_repo.py` 验证：
   - 当前状态应通过（因为 req-07 已同步）
   - 手动修改一个 scaffold 文件后再运行，应报错
6. 恢复手动修改，确保测试后状态干净

## Artifacts

- 更新后的 `lint_harness_repo.py`

## Dependencies

- 无
