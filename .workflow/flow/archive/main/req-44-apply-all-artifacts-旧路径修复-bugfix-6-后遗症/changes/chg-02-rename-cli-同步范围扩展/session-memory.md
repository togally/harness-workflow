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

## executing ✅

- `rename_requirement`（`workflow_helpers.py`）：在现有 artifacts/ mv 后追加 `.workflow/flow/requirements/{old_dir_name}` 探测 + 条件 mv（存在才动，AC-03）。
- 函数末尾追加 runtime 同步段：`current_requirement == old_id` → 写 `current_requirement_title`；`locked_requirement == old_id` → 写 `locked_requirement_title`；其它字段 verbatim 保留。
- 新测试文件 `tests/test_req44_chg02.py`（TC-01 ~ TC-05），5 用例全过。
