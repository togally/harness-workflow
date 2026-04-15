# Plan: chg-02

## Steps

1. 在临时项目创建多个 suggest，然后执行 `harness suggest --apply-all`
2. 验证所有 pending suggest 被正确转为 req
3. 更新 `README.md`，在 suggest 示例中增加 `--apply-all`
4. 同步 `scaffold_v2`
5. `pipx inject harness-workflow . --force`
6. 生成 done-report 并归档 req-12
