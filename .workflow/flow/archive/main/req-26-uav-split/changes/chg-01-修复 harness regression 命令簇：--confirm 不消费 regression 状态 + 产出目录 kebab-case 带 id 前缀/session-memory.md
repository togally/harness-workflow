# Session Memory

## 1. Current Goal

- Describe the current goal for this change.

## 2. Current Status

- Summarize what is already done.

## 3. Validated Approaches

- Record commands, checks, or decisions that already worked.

## 4. Failed Paths

- Attempt:
- Failure reason:
- Reminder: do not retry this blindly unless assumptions change.

## 5. Candidate Lessons

```markdown
### [date] [summary]
- Symptom:
- Cause:
- Fix:
```

## 6. Next Steps

- Add the next actions here.

## 7. Open Questions

- Add unresolved questions here.

## 执行记录

### 改动文件
- src/harness_workflow/slug.py：新增 slugify util
- src/harness_workflow/workflow_helpers.py：regression CLI 行为修复（+103/-7）
- tests/test_regression_helpers.py：9 个测试用例全过

### Self-check
- unittest: 9 passed, 0 failed
- slugify 覆盖 CJK、空格、标点、连续编号
- 未触碰 chg-02/03/04 范围

### 遗留 / 交接
- slug util 已就绪，chg-02 可直接 import 复用
- regression 目录命名 `reg-NN-<slug>`；runtime.current_regression 只存 `reg-NN`
