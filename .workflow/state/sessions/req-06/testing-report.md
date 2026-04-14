# Testing Report: req-06-done报告记录实现时长

## Test Date
2026-04-15

## Stage
ff 模式自举验证（executing → testing）

## Test Results

### AC-1: done-report.md 头部包含"实现时长"字段
- [x] 模板已定义在 `done.md` 中
- [ ] 待 done 阶段实际生成报告时验证

### AC-2: 时长的计算口径在 `stages.md` 中有明确定义
- [x] 总时长 = requirement_review 开始 ~ done 结束 ✅
- [x] 分阶段时长 = 相邻 stage 时间戳之差 ✅
- [x] 文档位置：`stages.md` 中新增"需求实现时长记录"章节 ✅

### AC-3: 数据来源稳定可靠
- [x] 选定方案 A：`state/requirements/{id}.yaml` ✅
- [x] req-06 yaml 已添加 `started_at` 和 `stage_timestamps` ✅
- [x] 降级策略已定义（`created_at` 降级、缺失阶段显示 N/A）✅

### AC-4: 示例报告验证了时长记录的正确性
- [ ] 待 done 阶段生成实际报告后验证

### AC-5: 涉及 yaml 结构变更的文档已同步更新
- [x] `stages.md` 已包含新的字段规范说明 ✅

## chg-01 ~ chg-02 内部测试

### chg-01: 实现时长定义与数据采集机制
- [x] 计算口径文档化 ✅
- [x] 数据采集方案已选定 ✅
- [x] yaml 字段规范已更新 ✅
- [x] 降级策略已定义 ✅

### chg-02: 报告模板更新
- [x] `done.md` 包含时长记录要求 ✅
- [x] 提供模板示例 ✅
- [x] 格式统一可读 ✅

## Conclusion

**chg-01 ~ chg-02 设计文档全部通过测试。**

需要继续完成 done 阶段的实际报告生成，以最终验证 AC-1 和 AC-4。
