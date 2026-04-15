# Plan: chg-04

## Steps

1. 在临时项目测试：
   - `harness suggest "测试建议"`
   - `harness suggest --list`
   - `harness suggest --apply sug-01`
   - `harness suggest --delete sug-01`
2. 更新 `README.md` 和/或 `stages.md`，增加 suggest 命令说明
3. 同步 `scaffold_v2`
4. `pipx inject harness-workflow . --force`
5. 生成 done-report 并归档

## Artifacts

- 测试记录
- 更新后的文档
- 归档后的 req-10

## Dependencies

- 依赖 chg-01、chg-02、chg-03
