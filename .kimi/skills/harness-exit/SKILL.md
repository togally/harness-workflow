---
name: harness-exit
description: "Run harness exit in the Harness workflow"
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

- leave harness conversation mode cleanly
- once exited, do not keep enforcing the current harness node as the only valid context
- do not mutate requirement, change, plan, or runtime stage beyond clearing the conversation lock