# Session Memory

## 1. Current Goal

- Change 3: Extend the hook system with `testing` and `acceptance` stage hooks, and a main/subagent detection hook.

## 2. Current Status

- COMPLETED. All 11 new hook files have been registered in `HOOK_TIMINGS` in `core.py`.

## 3. Validated Approaches

- New hooks are added directly as items in the `HOOK_TIMINGS` list in `src/harness_workflow/core.py`.
- The `hook_managed_contents` function automatically generates all managed file paths from `HOOK_TIMINGS`, so no separate file creation is needed — registering in `HOOK_TIMINGS` is sufficient.
- Chinese curly-quote characters (`"..."`) must not be used inside Python double-quoted strings; they cause `SyntaxError`. Use plain words or ASCII quotes instead.
- Verification command: `python3 -c "import sys; sys.path.insert(0, 'src'); from harness_workflow.core import _managed_file_contents; print('OK')"`

## 4. Failed Paths

- Attempt: Used Chinese curly-quote characters (`"Accepted"`) directly inside Python double-quoted strings.
- Failure reason: Python parser treats `"` as a string terminator, causing SyntaxError.
- Reminder: Always use plain ASCII or escape sequences when embedding quote-like characters inside Python string literals.

## 5. Candidate Lessons

```markdown
### 2026-04-11 Hook registration pattern in harness-workflow
- Symptom: Needed to add new hook files but unsure where to register them.
- Cause: Hooks are not stored as static files; they are generated at install time from `HOOK_TIMINGS` in `core.py`.
- Fix: Add new hook items directly to the relevant timing's `items` list in `HOOK_TIMINGS`. The `hook_managed_contents` function handles generation automatically.
```

## 6. Next Steps

- Run `harness update` or equivalent to regenerate managed hook files in the active workflow directory.
- Verify generated files appear under `workflow/context/hooks/` for each new hook.

## 7. Open Questions

- None.
