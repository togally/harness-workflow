# Plan: chg-01

## Steps

1. 在 `stages.md` 或相关文档中记录 suggest 的存储规范
2. 定义文件格式示例：
   ```markdown
   ---
   id: sug-01
   created_at: "2026-04-15"
   status: pending
   ---
   
   给 done 报告增加自动发送邮件功能
   ```
3. 定义 ID 生成规则：扫描 `.workflow/flow/suggestions/` 下所有 `sug-NN-*.md`，取最大 NN +1

## Artifacts

- 文档化的 suggest 存储规范（可写入 `stages.md` 或新增 `suggest.md`）

## Dependencies

- 无
