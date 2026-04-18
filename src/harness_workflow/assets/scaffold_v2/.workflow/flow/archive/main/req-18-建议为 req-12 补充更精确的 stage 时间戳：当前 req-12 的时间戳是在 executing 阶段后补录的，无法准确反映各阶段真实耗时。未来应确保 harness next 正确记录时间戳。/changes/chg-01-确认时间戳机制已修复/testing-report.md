# Testing Report: chg-01

## Test Cases

1. **Req-14 coverage check**
   - `workflow_next` in `core.py` now writes `stage_timestamps[next_stage]` for every stage transition, not just `done`

2. **Live verification via req-17**
   - Checked `.workflow/flow/archive/main/req-17-.../state.yaml`
   - `stage_timestamps` contains entries for `testing`, `acceptance`, and `done` with distinct ISO8601 timestamps

## Issues Found

None.
