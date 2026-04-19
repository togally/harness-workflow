# Plan: chg-01

## Steps

1. 读取 `cli.py`，在 `suggest_parser` 中为 `--apply-all` 新增可选的 `--title` 参数
2. 读取 `core.py` 中的 `apply_all_suggestions`，重构其逻辑：
   - 先扫描并收集所有 `status: pending` 的 suggest（ID + 标题）
   - 若传入 `title` 参数则使用之，否则生成默认标题 `"批量建议合集（N条）"`
   - 用收集到的第一条 suggest 的标题（或固定前缀）作为 `create_requirement` 的 title
   - 调用 `create_requirement(root, title)` 生成一个 req
   - 若 `create_requirement` 返回 0，则删除所有被处理的 suggest 文件
   - 收集删除列表和失败列表
3. 更新输出格式：
   ```
   Packed N suggestion(s) into req-XX:
     - sug-01: 对话摘要...
     - sug-02: 提交git...
   ```
4. 本地语法检查（`py_compile`）

## Artifacts

- 更新后的 `src/harness_workflow/cli.py`
- 更新后的 `src/harness_workflow/core.py`
