# Testing Report: req-05-ff功能

## Test Date
2026-04-15

## Stage
ff 模式自举验证（executing → testing）

## Test Results

### AC-1: `stages.md` 中 `harness ff` 的完整行为定义
- [x] 适用条件（requirement_review / planning）
- [x] 自动推进规则（各 stage 完成判定条件 + 推进逻辑）
- [x] AI 自主决策边界（可自行决定 / 必须暂停求援）
- [x] ff 失败时的处理路径（正常终止 / 异常终止 / 平台错误恢复引用）

### AC-2: `runtime.yaml` 支持记录 ff 模式状态
- [x] `ff_mode` 字段已添加（布尔值）
- [x] `ff_stage_history` 字段已添加（数组）

### AC-3: 主 agent 的 ff 模式职责补充
- [x] `WORKFLOW.md` 中新增 "ff 模式协调职责" 小节
- [x] 包含自动推进、session-memory 保存、边界监控、异常处理职责

### AC-4: 端到端自举验证（部分，继续中）
- [x] req-05 当前已处于 executing 阶段且 chg-01~03 已完成
- [ ] 需完成 testing → acceptance → done → archive 的全流程

### AC-5: `constraints/recovery.md` 新增恢复路径
- [x] "平台级错误 / 会话损坏" 恢复条目已新增
- [x] "skill 缺失处理路径" 条目已新增

### AC-6: 经验沉淀（待完成）
- [ ] 需更新 `context/experience/` 下经验文件

## chg-01 ~ chg-03 内部测试

### chg-01: `harness ff` 语义增强设计
- [x] 启动条件 ✅
- [x] 自动推进规则 ✅
- [x] AI 自主决策边界 ✅
- [x] 失败处理路径 ✅
- [x] 逻辑一致性检查通过 ✅

### chg-02: 自动推进与状态流转机制
- [x] `runtime.yaml` 包含 `ff_mode` ✅
- [x] `runtime.yaml` 包含 `ff_stage_history` ✅
- [x] stages.md 中定义自动推进逻辑 ✅
- [x] stages.md 中定义 session-memory 规范 ✅
- [x] stages.md 中定义暂停/退出机制 ✅

### chg-03: 角色文件与约束更新
- [x] `WORKFLOW.md` 已更新 ✅
- [x] `planning.md` 已补充 ff 说明 ✅
- [x] `executing.md` 已补充 ff 说明 ✅
- [x] `testing.md` 已补充 ff 说明 ✅
- [x] `acceptance.md` 已补充 ff 说明 ✅
- [x] `requirement-review.md` 已补充 ff 说明 ✅
- [x] `regression.md` 已补充 ff 说明 ✅
- [x] `constraints/boundaries.md` 新增 ff 决策边界 ✅
- [x] `constraints/recovery.md` 新增平台错误恢复 ✅
- [x] `constraints/recovery.md` 新增 skill 缺失处理 ✅

## Conclusion

**chg-01 ~ chg-03 全部通过内部测试。**

需要继续完成：
1. chg-04 端到端自举验证（testing → acceptance → done → archive）
2. 经验文件沉淀
