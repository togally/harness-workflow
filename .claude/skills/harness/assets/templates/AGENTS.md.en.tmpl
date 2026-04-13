# AGENTS.md

This repository uses the Harness workflow for agent collaboration.

## Read First

1. Before requirement, change, plan, or execution work, read `workflow/context/rules/workflow-runtime.yaml`
2. Use `current_version` to read the active version `meta.yaml`
3. Read `workflow/memory/constitution.md`
4. Read `workflow/context/experience/index.md`
5. Read `workflow/context/rules/risk-rules.md`
6. Load only matching experience files
7. Read `workflow/context/rules/agent-workflow.md`, `workflow/context/rules/development-flow.md`, and `workflow/context/hooks/README.md`
8. Read `workflow/context/project/project-overview.md` and `workflow/context/team/development-standards.md` as needed
9. When entering a new node, switching submodules, or noticing that old context no longer affects the next task, run a `context-maintenance` check first: prefer `/clear` for irrelevant context and `/compact` for still-useful but compressible context
10. After `/clear` or `/compact`, re-read `workflow-runtime.yaml`, the current version `meta.yaml`, and the matched hooks
11. If `current_version` is missing, runtime/config disagree, version `meta.yaml` is missing, or the workflow is blocked, stop immediately and ask for repair instead of improvising a manual fallback flow
12. Before each stage starts a concrete task, re-index experience; after each stage completes, check whether new lessons should be captured or fused
13. If the human is unhappy with a completed result, start `harness regression "<issue>"` first and confirm the problem before creating new work
14. Every completed change must include `mvn compile`; every completed requirement must include successful project startup validation
15. If startup logs, compile output, or test failures are available locally, the AI should inspect them first
16. If compilation fails, startup fails, or repair still needs human input, move into regression and fill the related change `regression/required-inputs.md` first, then ask the human to complete it
17. If the current stage is `requirement_review`, even a detailed implementation prompt must be treated as discussion input only; do not start coding yet
18. If `workflow-runtime.yaml` shows `conversation_mode: harness`, keep every following reply inside the locked `version`, `stage`, and workflow node until the human explicitly runs `harness exit`
19. `testing` and `acceptance` are independent stages that follow `executing` and precede `done` — do not skip them; each has its own directory under the active version
20. `harness status` displays the full stage progress tree including testing and acceptance progress
21. Experience files are organized by category (`stage/`, `tool/`, `business/`, `architecture/`, `debug/`, `risk/`) — load only the category relevant to the current task

## Main Entry

- `harness version "<name>"`
- `harness active "<name>"`
- `harness use "<name>"`
- `harness enter`
- `harness exit`
- `harness status`
- `harness next`
- `harness ff`
- `harness requirement "<title>"`
- `harness change "<title>"`
- `harness plan "<change>"`
- `harness regression "<issue>"`
- `harness rename version|requirement|change "<old>" "<new>"`
- `harness archive "<requirement>"`
- `harness update`

If workflow state is missing or inconsistent, stop and require `harness active "<version>"` or restoration of the missing workflow files before continuing.
