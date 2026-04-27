# Session Memory

## 1. Current Goal

- 实现 chg-01（verdict stage work-done gate + workflow_next 集成）：helper + while 插桩 + lint + 8 新用例。

## 2. Current Status

- 工作完成 ✅

## 3. Validated Approaches

- `_is_stage_work_done` helper 在 workflow_helpers.py `_get_exit_decision` 之后 / `workflow_next` 之前插入。
- while 插桩：`if no_user_decision and not same_role and not _is_stage_work_done(...)` break。
- `acceptance` 检查用 regex `^#{1,3}\s*§?结论` 而非 `"结论" in text`（避免"无结论段落"误匹配）。
- `check_stage_work_completion` + `run_contract_cli` 新增 `stage-work-completion` 分支。
- 9 用例（含 TC-03b 单元测试）全过，pre-existing failures 不变（test_smoke_req28 / test_smoke_req29）。

## 4. Failed Paths

- `"结论" in text` 误匹配"无结论段落"，导致 TC-03b FAIL → 改为 regex 段标题检测。

## 5. Candidate Lessons

```markdown
### 2026-04-25 §结论 子串匹配易误命中否定词
- Symptom: acceptance "无结论段落" 含 "结论" 子串被误判为有 §结论
- Cause: 简单 `in` 检查不区分是否是段落标题
- Fix: 改用 regex `^#{1,3}\s*§?结论` 匹配标题行
```

## 6. Next Steps

- 主 agent 接手 testing 验收阶段。

## 7. Open Questions

- 无。

## executing ✅

- 实现完成时间：2026-04-25
- 关键文件：`src/harness_workflow/workflow_helpers.py`（+`_is_stage_work_done` helper + while gate）、`src/harness_workflow/validate_contract.py`（+`check_stage_work_completion` + `run_contract_cli` 分支）
- 新测试文件：`tests/test_workflow_next_workdone_gate.py`（9 用例，含 TC-03b 单元补强）
- 全量回归：591 pass / 38 skip / 0 new fail（pre-existing: test_smoke_req28 + test_smoke_req29）
- scaffold diff：无（src/ 改动不涉及 .workflow/ 树）

## executing（重做）✅

- 重做时间：2026-04-25（git restore 事故后 Sonnet 4.6 重做）
- BUG-01 修复：gate 插桩位置从 while 循环内移至第一格转换前，current_stage 无产物时 return 0 不跳
- 关键修改：
  - `_is_stage_work_done` helper：regex `^#{1,3}\s*§?结论` 替代 `"结论" in text` 子串匹配
  - `workflow_next` 第一格前 gate check（`_first_hop_exit` + `_first_hop_same_role` + `_is_stage_work_done`）
  - while 内 gate check 保留（防多格连跳）
  - `check_stage_work_completion` + `run_contract_cli stage-work-completion` 分支
- TC 修正：TC-02 / TC-03 / TC-06 断言从 buggy 行为改为正确行为（stage 停在 current）
- 全量回归：459 pass / 38 skip / 1 pre-existing fail（test_smoke_req28）
- dogfood 实跑：testing 无 test-report → 停 testing ✓；有 test-report（§结论）→ 跳 acceptance 停 ✓
- runtime stage 保持 testing（主 agent 接手 testing 验收）
