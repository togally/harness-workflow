# Testing Report: chg-02

## Test Cases

1. **Syntax check**
   - `python3 -m py_compile src/harness_workflow/core.py src/harness_workflow/cli.py` — passed

2. **`harness validate` on incomplete requirement**
   - Ran `harness validate` for req-14 (before creating reports)
   - Output correctly listed three changes missing `testing-report.md` and `acceptance-report.md`
   - Exit code was 1

3. **CLI integration**
   - `harness validate --help` shows the new subcommand

## Issues Found

None.
