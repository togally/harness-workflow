# Change: chg-03

## Title

端到端验证

## Goal

使用 req-06 自身验证实现时长记录机制，确保从 requirement_review 到 done 的全流程中，时长数据被正确采集并展示在 done 报告中。

## Scope

**包含**：
- 验证 `state/requirements/req-06-done报告记录实现时长.yaml` 中的时间字段是否正确
- 验证 `done-report.md` 头部的时长记录是否准确、格式统一
- 记录验证过程中的问题和改进建议

**不包含**：
- 修改验证范围外的其他需求报告

## Acceptance Criteria

- [ ] req-06 的 `done-report.md` 头部包含准确的实现时长记录
- [ ] 时长数据来源清晰可追溯
- [ ] 验证结果记录到 session-memory
