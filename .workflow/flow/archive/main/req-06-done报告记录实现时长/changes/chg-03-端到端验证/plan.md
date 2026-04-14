# Plan: chg-03

## Steps

1. 等待 chg-01 和 chg-02 完成
2. 在 executing 阶段实现 chg-01 和 chg-02 的文档/配置更新
3. 在 testing 阶段检查时间字段和报告模板
4. 在 done 阶段生成 `done-report.md`，核对头部时长记录：
   - 总时长是否合理
   - 各阶段时长是否可计算
   - 格式是否符合 chg-02 模板
5. 记录验证结果和改进建议到 session-memory

## Artifacts

- req-06 的 `done-report.md`（包含时长记录）
- 验证记录

## Dependencies

- 依赖 chg-01、chg-02
