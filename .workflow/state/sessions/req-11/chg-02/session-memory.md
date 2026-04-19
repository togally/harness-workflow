# Session Memory: chg-02

## Change
实现建议自动提取与 suggest 创建

## Status
✅ 已完成

## Steps
- [x] 在 `core.py` 中新增 `extract_suggestions_from_done_report(root, req_id)` 函数
- [x] 实现 done-report.md 中 `## 改进建议` 区块的解析逻辑
- [x] 支持提取 `> **建议**` 引用块、`- ` 列表项、`1. ` 有序列表项
- [x] 在 `workflow_next` 中，当 stage 推进到 done 时自动调用提取函数
- [x] 修复 `save_simple_yaml` / `load_simple_yaml` 不支持 dict 的底层 bug
- [x] 修复 `_migrate_state_files` 对旧版字符串 `stage_timestamps` 的处理
- [x] 临时项目端到端测试通过，4 条建议成功自动转为 suggest

## Internal Test
- [x] `harness next` 进入 done 后自动创建 suggest ✅
- [x] 4 条不同格式的建议均被正确提取 ✅
- [x] 旧 state 文件迁移后不再报错 ✅
