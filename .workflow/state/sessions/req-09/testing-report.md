# Testing Report: req-09-README优化

## Test Date
2026-04-15

## Test Results

### AC-1: README 实践原则部分表述清晰
- [x] "实践原则"已前置到 Why 之后、Installation 之前 ✅
- [x] 7 条原则完整保留，表述清晰 ✅

### AC-2: README 明确引导到 `.workflow/` 查找详细规则
- [x] "Where Detailed Rules Live" 段落已重写 ✅
- [x] 明确列出了 `WORKFLOW.md`、`.workflow/context/index.md`、roles、experience、constraints、stages.md、tools 等入口 ✅
- [x] 增加了 Tip 提示用户无需背诵目录树 ✅

### AC-3: README 中无详细目录结构列表
- [x] 已删除底部的 "Repository Structure" 详细列表（含 context/、tools/、flow/、state/、evaluation/、constraints/ 的逐层展开）✅
- [x] 仅保留高层的 "Six-Layer Architecture" 示意图 ✅

### AC-4: README 安装说明包含强制安装
- [x] Installation 部分已包含 `harness install --force` 及其使用场景说明 ✅

## Conclusion

**所有 AC 均已满足，测试通过。**
