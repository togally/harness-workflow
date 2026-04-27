# Regression Required Inputs — chg-01（verdict stage work-done gate + workflow_next 集成）

> 来源：testing 阶段 dogfood 调查 + source 代码丢失事故（2026-04-25）
> 优先级：P0 Critical（双 bug）

---

## 1. Current Problem

### BUG-01（P0）：gate 插桩位置错——第一格跳转无 gate 检查

**Issue summary**：
`harness next` 从 testing 出发，缺 test-report.md 时仍跳到 acceptance（应停在 testing）。
work-done gate 仅在 while 循环内（line 7597-7603）检查已落点 `from_s`，未覆盖第一格无条件写出（line 7575 `_write_stage_transition`）。
AC-01 / AC-02 均未满足。

**Related regression**：本 chg-01 的 dogfood 自验
**Linked change**：chg-01（verdict stage work-done gate + workflow_next 集成）

**dogfood 实测**：
```bash
# runtime stage=testing，req-45 flow dir 无 test-report.md
harness next
# 输出：Workflow advanced to acceptance  ← 错误，应停在 testing
```

**根因（精确定位）**：

`workflow_helpers.py` workflow_next 函数内：

```python
# line 7570-7577（问题区域）：
from_s = current_stage   # = "testing"
to_s = next_stage        # = "acceptance"
walk_idx = sequence.index(to_s)

_write_stage_transition(from_s, to_s, prev_iso)   # 第一格无条件写出！无 gate 检查
from_s = to_s   # from_s = "acceptance"

# while 循环 gate（line 7597-7603）只检查 from_s（已落点），不检查出发点 testing
while ...:
    if no_user_decision and not same_role and not _is_stage_work_done(from_s, ...):
        break
```

**修复方向（建议 regression/executing 采用方向 A）**：

在第 7575 行 `_write_stage_transition` 调用之前，插入出发 stage 的 work-done 检查：

```python
# 新增：在 _write_stage_transition(from_s, to_s, prev_iso) 之前
current_exit_for_first_hop = _get_exit_decision(current_stage, stage_policies)
if (current_exit_for_first_hop in _AUTO_JUMP_DECISIONS
        and not same_role  # same_role 路径不加 gate（保 bugfix-5（同角色跨 stage 自动续跑硬门禁） 契约）
        and not _is_stage_work_done(current_stage, root, operation_target, operation_type)):
    # 出发 stage 工作未完成，停止推进（不翻第一格）
    print(f"Stage {current_stage} 工作未完成，请先完成当前阶段工作再推进。", file=sys.stderr)
    return 0

_write_stage_transition(from_s, to_s, prev_iso)  # 原有逻辑
```

**同步修正 TC-02**：修复后 TC-02 应断言 `stage=testing`（不跳 acceptance），当前断言 `stage=acceptance` 是写给错误实现的。

---

### BUG-02（P0）：source 代码丢失——testing 阶段 git restore 事故

**Issue summary**：
testing 阶段执行 revert dry-run 时，`git revert --no-commit e7a2bfd` 因 working tree dirty 报错，
随后执行 `git restore .` 还原，导致 executing 阶段落地的 source 改动全部丢失：
- `src/harness_workflow/workflow_helpers.py`：`_is_stage_work_done` helper + while gate 插桩丢失
- `src/harness_workflow/validate_contract.py`：`check_stage_work_completion` + `run_contract_cli` 新分支丢失

**事故后状态**：
- `python3 -m pytest tests/test_workflow_next_workdone_gate.py`：ImportError（0/9）
- `harness next`：原 over-chain bug 重现（无 gate 保护）

**恢复方案（建议 regression/executing）**：
按 session-memory.md §3 Validated Approaches 和 plan.md §3 实施步骤，重新实现：
1. `_is_stage_work_done` helper（workflow_helpers.py，`_get_exit_decision` 之后）
2. while gate 插桩（workflow_next while 块，BUG-01 修复版本，检查 current_stage 第一格）
3. `check_stage_work_completion` + `run_contract_cli stage-work-completion` 分支（validate_contract.py）
4. 重跑 9 用例（含 TC-02 断言修正为 `stage=testing`）
5. 全量回归确认 591 pass

---

## 2. Required Human Inputs

| Item | Required | Notes |
|------|---------|-------|
| Configuration | no | 无需人工配置 |
| Test data | no | test fixture 由 pytest tmp_path 自生成 |
| Account details | no | - |
| External dependency details | no | - |

---

## 3. Human Response Section

（无需人工填写，regression/executing 可直接按上述方向修复）

---

## 4. Next Step

1. 主 agent 确认本 required-inputs.md 后，启动 `harness regression "gate 插桩位置错 + source 代码丢失"`
2. regression 诊断确认根因 → 路由 executing 阶段重新实现
3. executing 完成后返回 testing 重跑验证
