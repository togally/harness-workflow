# Testing Report: chg-01

## Test Cases

1. **Syntax check**
   - `python3 -m py_compile src/harness_workflow/core.py` — passed

2. **Req state update on `harness next`**
   - Ran `harness next` from `acceptance` to `done`
   - Checked `.workflow/state/requirements/req-14-*.yaml`
   - Result: `stage: done`, `status: done`, `stage_timestamps.done` populated with ISO8601 UTC timestamp

3. **Match logic fix verification**
   - Debug script confirmed `req_file.stem` matching works for long requirement titles

## Issues Found

None.
