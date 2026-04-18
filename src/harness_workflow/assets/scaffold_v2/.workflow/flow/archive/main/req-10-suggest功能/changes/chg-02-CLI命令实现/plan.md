# Plan: chg-02

## Steps

1. 读取 `cli.py`，找到命令注册的位置，新增 `suggest` 子命令解析
2. 读取 `core.py`，在合适位置新增以下函数：
   - `create_suggestion(root, content, title)`
   - `list_suggestions(root)`
   - `apply_suggestion(root, suggest_id)`
   - `delete_suggestion(root, suggest_id)`
3. `create_suggestion`：生成 slug，确定下一个 ID，写入 `.workflow/flow/suggestions/sug-NN-{slug}.md`
4. `list_suggestions`：读取所有 suggest 文件，输出表格
5. `apply_suggestion`：
   - 读取指定 suggest 文件
   - 调用 `create_requirement(root, title, requirement_id=None)` 创建需求
   - 将 suggest 的 status 改为 applied
   - 输出创建成功的 req-id
6. `delete_suggestion`：删除指定 suggest 文件
7. 在 `cli.py` 中注册 `suggest` 命令并调用上述函数
8. 运行本地测试验证

## Artifacts

- 更新后的 `src/harness_workflow/cli.py`
- 更新后的 `src/harness_workflow/core.py`

## Dependencies

- 依赖 chg-01 的存储规范
