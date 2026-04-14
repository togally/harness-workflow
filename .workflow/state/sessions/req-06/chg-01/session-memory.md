# Session Memory: chg-01

## Change
实现时长定义与数据采集机制

## Status
✅ 已完成

## Steps
- [x] 评估现有状态文件结构
- [x] 选定方案 A（`state/requirements/{id}.yaml` 作为数据源）
- [x] 在 `stages.md` 中增加"需求实现时长记录"章节
- [x] 定义计算口径、数据字段、采集规则和降级策略
- [x] 更新 req-06 的 `state/requirements/req-06-done报告记录实现时长.yaml`，添加 `started_at` 和 `stage_timestamps`

## Internal Test
- [x] `stages.md` 包含时长定义 ✅
- [x] `stages.md` 包含数据字段规范 ✅
- [x] `stages.md` 包含降级策略 ✅
- [x] req-06 yaml 已更新 ✅

## Notes
方案 A 被选定为唯一方案，因为它最持久化和需求中心化。无需额外更新 `runtime.yaml` 结构。
