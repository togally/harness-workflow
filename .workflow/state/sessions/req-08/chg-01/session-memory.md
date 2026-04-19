# Session Memory: chg-01

## Change
lint 增加 scaffold_v2 同步检查

## Status
✅ 已完成

## Steps
- [x] 读取 `lint_harness_repo.py`
- [x] 新增 `_check_scaffold_v2_sync()` 函数
- [x] 检查 `stages.md`、`WORKFLOW.md`、`CLAUDE.md` 的同步状态
- [x] 在主 lint 流程中调用并输出修复提示
- [x] 本地运行验证通过

## Internal Test
- [x] `python3 lint_harness_repo.py --root .` 通过 ✅
- [x] 手动修改 scaffold 后报错，恢复后通过 ✅
