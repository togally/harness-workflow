# Plan: chg-02

## Steps

1. 更新 `README.md`：在 `harness archive` 说明中增加 "归档后若位于 Git 仓库，会提示是否自动提交"
2. 同步 `src/harness_workflow/assets/scaffold_v2/README.md`
3. 在临时目录初始化 Git 仓库并 `harness init`，创建并归档一个需求，验证提示和提交行为
4. `pipx inject harness-workflow . --force`
5. 产出 testing-report 和 acceptance-report

## Artifacts

- 更新后的 `README.md`
- 更新后的 `src/harness_workflow/assets/scaffold_v2/README.md`
