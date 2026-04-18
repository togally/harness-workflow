# Plan: chg-01

## Steps

1. 读取 `cli.py`，在 `suggest_parser` 中新增 `--apply-all` 参数
2. 读取 `core.py`，在 `create_suggestion` 附近新增 `apply_all_suggestions(root)`：
   - 扫描 `.workflow/flow/suggestions/` 下所有 `sug-*.md`
   - 读取 frontmatter，过滤 `status: pending`
   - 对每条 pending suggest，提取 body 第一行作为 title
   - 调用 `create_requirement(root, title)`
   - 成功后更新 suggest 状态为 `applied`
   - 收集成功列表和失败列表
3. 在 `cli.py` 的 `suggest` 命令分支中增加 `--apply-all` 的处理
4. 输出格式：
   ```
   Applied N suggestion(s):
     - sug-01 → req-01-xxx
     - sug-02 → req-02-yyy
   Failed: M
   ```
5. 本地测试验证

## Artifacts

- 更新后的 `src/harness_workflow/cli.py`
- 更新后的 `src/harness_workflow/core.py`
