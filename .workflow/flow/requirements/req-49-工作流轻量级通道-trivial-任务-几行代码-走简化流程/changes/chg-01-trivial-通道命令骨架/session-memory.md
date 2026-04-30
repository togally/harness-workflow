# Session Memory — chg-01（trivial 通道命令骨架）

## 实施摘要

### Steps ✅

- ✅ Step 1：workflow_helpers.py 新增 TRIVIAL_SEQUENCE / VALID_TASK_TYPES / get_sequence_for_task_type / validate_stage / get_next_stage / is_terminal_stage
- ✅ Step 2：workflow_next 新增 trivial 分支；_FALLBACK_STAGES 加 trivial_define；_REGRESSION_ROUTE_VALID_STAGES 扩 TRIVIAL_SEQUENCE
- ✅ Step 3：create_trivial + apply_suggestion_as_trivial helper
- ✅ Step 4：cli.py 注册 trivial 子命令 + suggest --trivial flag
- ✅ Step 5：harness-manager.md §3.4 + §3.4.1 + scaffold_v2 mirror 同步
- ✅ Step 6：suggest --apply --trivial 路径（AC-06）
- ✅ Step 7：硬门禁自检

## 关键决策

1. **load_requirement_runtime 自愈修复**：trivial 任务使用 req-id 编号空间，原代码通过 id 前缀推断 operation_type 会把 "trivial" 覆盖为 "requirement"。增加 `_EXPLICIT_TYPES = {"trivial", "regression"}` 豁免，显式 operation_type 优先保留。

## 测试结果

38 tests passed（全绿）
