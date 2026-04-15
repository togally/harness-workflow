# Plan: chg-02

## Steps

1. 更新 `README.md`：
   - 在 Core Commands 表格中更新 `harness suggest --apply-all` 的描述
   - 在示例代码块中补充 `--apply-all [--title "..."]` 的用法
2. 同步 `src/harness_workflow/assets/scaffold_v2/README.md`
3. 在临时项目验证：
   - `harness init` 创建临时项目
   - 创建 2~3 条 suggest
   - 执行 `harness suggest --apply-all --title "测试打包标题"`
   - 验证：只生成 1 个 req、`.workflow/flow/suggestions/` 下原 suggest 文件已删除
4. `pipx inject harness-workflow . --force`
5. 产出 testing-report 和 acceptance-report

## Artifacts

- 更新后的 `README.md`
- 更新后的 `src/harness_workflow/assets/scaffold_v2/README.md`
