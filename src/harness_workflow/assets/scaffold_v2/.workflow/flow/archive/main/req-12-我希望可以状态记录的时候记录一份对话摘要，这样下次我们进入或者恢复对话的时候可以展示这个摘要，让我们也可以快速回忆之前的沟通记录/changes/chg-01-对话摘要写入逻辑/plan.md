# Plan: chg-01

## Steps

1. 检查 `core.py` 中是否有 `save_session_memory` 或类似函数
2. 确保各阶段切换时（特别是 done 阶段），session-memory 的 `## Stage 结果摘要` 区块完整记录了本轮工作
3. 如果没有自动写入逻辑，则在 `workflow_next` 或 done 阶段入口添加摘要补全逻辑
4. 本地验证：完成一个 req 后检查 session-memory 内容

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
