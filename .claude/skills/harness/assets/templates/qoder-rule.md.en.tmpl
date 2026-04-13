# Harness Workflow

This repository uses the Harness workflow for requirement, change, plan, execution, and regression work.

## Qoder Routing Rules

1. Before requirement, change, plan, execution, or regression work, read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Then read:
   - `workflow/context/rules/development-flow.md`
   - `workflow/context/rules/agent-workflow.md`
   - `workflow/context/rules/risk-rules.md`
   - `workflow/context/experience/index.md`
4. When entering a new node, switching submodules, or noticing that old context no longer affects the next task, run a `context-maintenance` check first: prefer `/clear` for irrelevant context and `/compact` for still-useful but compressible context
5. After `/clear` or `/compact`, re-read `workflow-runtime.yaml`, the current version `meta.yaml`, and the matched hooks
6. If `current_version` is missing, runtime/config disagree, version `meta.yaml` is missing, or the workflow is blocked, stop immediately and do not improvise a manual fallback flow
7. If `suggested_skill` is present, prefer it for the current stage

## Shared Entry

- root `AGENTS.md` is the cross-agent entrypoint
- `workflow/context/rules/*` stays the detailed rule source
- `workflow/versions/active/<version>/` stays the current version workspace

## Quality Gates

- every completed change must record `mvn compile`
- every completed requirement must record successful project startup validation
- if compilation fails or startup fails, enter regression first
- if repair still needs human-provided external input, fill the related change `regression/required-inputs.md` before asking the human
