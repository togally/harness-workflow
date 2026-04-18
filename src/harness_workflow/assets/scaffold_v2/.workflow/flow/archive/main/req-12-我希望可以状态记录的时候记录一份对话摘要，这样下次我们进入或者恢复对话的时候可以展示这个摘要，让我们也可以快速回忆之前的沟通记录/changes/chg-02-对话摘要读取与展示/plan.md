# Plan: chg-02

## Steps

1. 读取 `core.py` 中的 `enter_repo` 或 `harness_enter` 相关函数
2. 添加逻辑：如果有 `current_requirement`，读取 `.workflow/state/sessions/{req-id}/session-memory.md`
3. 提取 `## Stage 结果摘要` 或第一个 `##` 区块的内容，打印到 stdout
4. 更新 CLI 帮助文本（如有必要）
5. 本地验证：`harness enter` 时能看到摘要输出
6. 重新安装包

## Artifacts

- 更新后的 `src/harness_workflow/core.py`
- 更新后的 `src/harness_workflow/cli.py`（帮助文本）
