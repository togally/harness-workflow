# Plan: chg-05

## Steps

1. 汇总 chg-01 ~ chg-04 的所有发现和修复
2. 撰写验证报告，包含：
   - 执行摘要
   - 发现的问题清单
   - 根因分析
   - 修复动作
   - 改进建议
3. 在 `context/experience/tool/harness.md` 或新文件中增加经验：
   - "安装后必须验证模板版本"
   - "harness update 不会自动处理新增文件"
4. 生成 req-07 的 done-report.md
5. 执行 `harness archive req-07-验证项目实际使用情况`

## Artifacts

- 验证报告
- 更新的经验文件
- 归档后的 req-07

## Dependencies

- 依赖 chg-01 ~ chg-04 全部完成
