# Plan: chg-03

## Steps

1. 在 `README.md` 的命令表格中增加 `harness validate` 一行
2. 同步 `src/harness_workflow/assets/scaffold_v2/README.md`
3. 创建一个临时需求并 `harness next` 几次，验证 `stage_timestamps` 被正确写入
4. 运行 `harness validate` 检查输出
5. `pipx inject harness-workflow . --force`
6. 产出 testing-report 和 acceptance-report

## Artifacts

- 更新后的 `README.md`
- 更新后的 `src/harness_workflow/assets/scaffold_v2/README.md`
