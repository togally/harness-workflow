# Plan: chg-03

## Steps

1. 在临时项目中：
   - install harness
   - 创建需求并手动进入 done
   - 构造包含改进建议的 done-report.md
   - 触发 `extract_suggestions_from_done_report`
   - 验证 `.workflow/flow/suggestions/` 下出现 suggest 文件
2. 更新 `stages.md` 中 done 阶段的说明（如需要）
3. 同步 `scaffold_v2`
4. `pipx inject harness-workflow . --force`
5. 生成 done-report 并归档 req-11

## Artifacts

- 验证记录
- 更新后的文档
- 归档后的 req-11

## Dependencies

- 依赖 chg-01、chg-02
