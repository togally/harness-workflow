---
name: harness-next
description: "Run harness next in the Harness workflow"
---

## Hard Gate

Do not act until these three files have been read in order:
1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`
6. If `.kimi/skills/harness/SKILL.md` exists, follow the main Harness skill


Focus:

- explain the current stage, current task, and next action first
- then advance according to the actual state instead of assuming a fixed sequence
- if the version is already `ready_for_execution`, do not start implementation automatically; ask for confirmation or use `harness next --execute`
- if workflow state is incomplete, stop and require state repair first