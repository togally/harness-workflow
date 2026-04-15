# Plan: chg-02

## Steps

1. 在 `README.md` 的 `harness regression` 行增加 "结束时会自动沉淀经验文件到 `.workflow/context/experience/regression/`" 的说明
2. 同步 `src/harness_workflow/assets/scaffold_v2/README.md`
3. 本地创建一个临时 regression，运行 `harness regression --confirm` 验证经验文件生成
4. `pipx inject harness-workflow . --force`
5. 产出 testing-report 和 acceptance-report

## Artifacts

- 更新后的 `README.md`
- 更新后的 `src/harness_workflow/assets/scaffold_v2/README.md`
