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
- src/harness_workflow/workflow_helpers.py +319/-37（rename 三函数 + create_change slug 接入）
- src/harness_workflow/cli.py / tools/harness_rename.py +6/-6（bugfix choice）
- tests/test_rename_helpers.py：新增 5 个测试

### Self-check
- unittest: 5 passed, 0 failed
- 历史目录不迁移（AC-06 Excluded）
- 未动 chg-01/03/04/05 范围

### 遗留
- harness change 目录命名自本次起生效；旧目录保留（Excluded）
