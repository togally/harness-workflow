# Plan: chg-02

## Steps

1. 在 `README.md` 的 `harness validate` 行补充 "includes syntax check for Python files"
2. 同步 `src/harness_workflow/assets/scaffold_v2/README.md`
3. 临时创建一个包含语法错误的 `.py` 文件，运行 `harness validate` 验证检测
4. 删除临时错误文件，运行 `harness validate` 确认通过
5. `pipx inject harness-workflow . --force`
6. 产出 testing-report 和 acceptance-report

## Artifacts

- 更新后的 `README.md`
- 更新后的 `src/harness_workflow/assets/scaffold_v2/README.md`
