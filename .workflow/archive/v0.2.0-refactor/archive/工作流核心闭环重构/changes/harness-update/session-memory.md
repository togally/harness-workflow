# Session Memory

## 1. Current Goal

- Ensure `harness update` correctly migrates existing business projects with version boundary handling.

## 2. Current Status

- COMPLETED. All 6 tasks executed successfully.

### Task 1: `_required_dirs` verification
- All 6 experience subdirectories already present: `stage/`, `tool/`, `business/`, `architecture/`, `debug/`, `risk/`
- `testing/` and `acceptance/` are version-level dirs correctly created in `create_version` (lines 2985-2987), NOT in `_required_dirs`

### Task 2: `_managed_file_contents` verification
- All 6 new doc templates registered: `test-plan.md`, `test-cases.md`, `bug.md`, `acceptance-checklist.md`, `sign-off.md`, `self-test.md`
- 11 hook files registered via `hook_managed_contents(language)` call
- All experience category files registered for `stage/`, `tool/`, `risk/` subdirs

### Task 3: executing → testing version boundary warning
- Added warning detection block in `update_repo` after `repair_identifier_drift`
- When current version is in `executing` stage, appends warning to actions list
- Confirmed in `harness update --check` output: WARNING appears correctly

### Task 4: CLAUDE.md and AGENTS.md template updates
- Updated all 4 templates (CN + EN for both CLAUDE.md and AGENTS.md)
- Added 3 new items to "Read First"/"优先阅读" section:
  - `testing` and `acceptance` are independent stages after `executing`
  - `harness status` shows full stage progress tree
  - Experience files are categorized by `stage/`, `tool/`, `business/`, etc.

### Task 5: `harness update --check`
- No errors; new template files appear as "missing" (would be created)
- WARNING for executing stage appears correctly

### Task 6: `harness update`
- Update succeeded; all 6 new template files written to `workflow/templates/`
- WARNING for executing stage appears at end of output

### Task 7: Syntax verification
- `python3 -c "import sys; sys.path.insert(0, 'src'); from harness_workflow.core import update_repo, install_repo; print('OK')"` → OK

## 3. Validated Approaches

- `_required_dirs` check: grep for function definition and verify list
- Warning insertion: placed between `repair_identifier_drift` and `workflow_blockers` blocks
- Template update: append numbered items at end of "Read First" sections

## 4. Failed Paths

- None encountered.

## 5. Candidate Lessons

```markdown
### 2026-04-11 version boundary warning pattern
- When adding new stages to a workflow, always add migration detection in `update_repo`
- Use the `actions` list to surface warnings without blocking the update
- Place version-level dirs (testing, acceptance) in `create_version`, not `_required_dirs`
```

## 6. Next Steps

- change 5 is complete; all 7 tasks done
- Ready for testing stage

## 7. Open Questions

- None.
