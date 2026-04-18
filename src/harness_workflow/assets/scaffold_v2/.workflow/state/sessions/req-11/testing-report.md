# Testing Report: req-11-done阶段建议自动转suggest

## Test Date
2026-04-15

## Test Results

### AC-1: `done.md` 中包含"将改进建议写入 suggest 池"的检查项
- [x] `done.md` 中已新增"建议转 suggest 池"段落和完成前检查项 ✅

### AC-2: `core.py` 中实现了从 `done-report.md` 提取建议并自动创建 suggest 的函数
- [x] `extract_suggestions_from_done_report` 已实现 ✅
- [x] `workflow_next` 进入 done 后自动调用 ✅

### AC-3: 完整需求走完后，`.workflow/flow/suggestions/` 下能自动出现 suggest 文件
- [x] 临时项目测试：构造包含 4 条建议的 done-report → `harness next` → 自动创建 4 个 suggest 文件 ✅
- [x] `harness suggest --list` 验证全部正确列出 ✅

### AC-4: 文档已更新
- [x] `done.md` 和 `WORKFLOW.md` 已更新 ✅
- [x] `scaffold_v2` 已同步 ✅

## 额外修复

- 修复了 `save_simple_yaml` / `load_simple_yaml` 不支持 `dict` 的底层 bug
- 修复了 `_migrate_state_files` 对字符串类型 `stage_timestamps` 的处理

## Conclusion

**所有 AC 满足，测试通过。**
