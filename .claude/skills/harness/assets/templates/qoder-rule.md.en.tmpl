# Harness Workflow

This repository uses the current Harness workflow for requirements, stage routing, and acceptance flow.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.

If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

## Qoder Routing Rules

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Read `.workflow/state/runtime.yaml`
4. Follow `.workflow/context/index.md` to load the role, experience, and constraint files for the current stage
5. If `conversation_mode: harness` or a requirement/stage lock is present, keep every reply inside the locked node
6. If `runtime.yaml` is missing, `current_requirement` is empty, or `stage` is missing or invalid, stop and require state repair before continuing
7. Before entering a new node, switching submodules, or when old context no longer affects the next step, run a context-maintenance check first: prefer `/clear` for irrelevant context and `/compact` for still-useful but compressible context

## Shared Entry

- the root `AGENTS.md` remains the cross-agent entrypoint
- `WORKFLOW.md -> .workflow/context/index.md -> .workflow/state/runtime.yaml` is the only primary route
- `.workflow/flow/requirements/<requirement>/` is the working document area
- `.workflow/state/` is the runtime state area

## Quality Gates

- do not skip either `testing` or `acceptance`
- if the human is unhappy with a result, start `harness regression "<issue>"` first
- if compilation fails, startup fails, or external input is still required, enter regression before proceeding
