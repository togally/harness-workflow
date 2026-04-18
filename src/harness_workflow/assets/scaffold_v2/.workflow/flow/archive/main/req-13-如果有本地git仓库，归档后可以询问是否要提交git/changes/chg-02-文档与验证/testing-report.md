# Testing Report: chg-02

## Test Cases

1. **README update**
   - `README.md` table row for `harness archive` now includes "in a Git repo, prompts to auto-commit"

2. **Scaffold README sync**
   - `src/harness_workflow/assets/scaffold_v2/README.md` updated with the same text

3. **Integration verification**
   - Same temp Git repo test as chg-01 confirms end-to-end behavior

4. **Package reinstall**
   - `pipx inject harness-workflow . --force` completed successfully

## Issues Found

None.
