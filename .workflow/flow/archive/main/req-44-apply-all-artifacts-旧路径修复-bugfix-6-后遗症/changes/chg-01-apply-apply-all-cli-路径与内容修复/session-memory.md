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

- 新增 `_append_sug_body_to_req_md` helper（`workflow_helpers.py` line ~4300）：按 `_use_flow_layout(req_id)` 分支选路径，原子 tmp→replace 写入，幂等聚合 `## 合并建议清单` 段。
- `apply_suggestion`：title 改从 sug frontmatter `title:` 字段取（AC-02），创建 req 后调 helper 写 body；写失败不阻断 sug archive。
- `apply_all_suggestions`：废弃旧 `resolve_requirement_root / req_md` 硬路径，改逐条调 `_append_sug_body_to_req_md`，FileNotFoundError → abort + stderr，保留 sug 不 unlink（AC-01）。
- 新测试文件 `tests/test_req44_chg01.py`（TC-01 ~ TC-06），6 用例全过。
