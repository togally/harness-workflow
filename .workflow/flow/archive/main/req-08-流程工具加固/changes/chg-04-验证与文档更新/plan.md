# Plan: chg-04

## Steps

1. 运行 `python3 src/harness_workflow/assets/skill/scripts/lint_harness_repo.py` 验证 lint 检查
2. 创建临时项目，写入旧格式 `runtime.yaml` 和 `requirements/*.yaml`
3. 运行修复后的 `harness update`，验证迁移结果
4. 在临时项目中创建一个假需求并执行 `harness archive`，验证残留目录被清理
5. 更新 `stages.md` 中 `harness update` 和 `harness archive` 的说明
6. 重新打包安装 `pipx inject harness-workflow . --force`
7. 生成 req-08 的 done-report.md
8. 执行 `harness archive req-08-流程工具加固`

## Artifacts

- 验证记录
- 更新后的 `stages.md`
- done-report.md
- 归档后的 req-08

## Dependencies

- 依赖 chg-01、chg-02、chg-03
