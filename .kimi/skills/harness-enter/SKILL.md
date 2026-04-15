---
name: harness-enter
description: "Run harness enter in the Harness workflow"
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

- enter harness conversation mode at the current version and current workflow node
- after entering, keep the discussion inside the current harness stage instead of drifting into unrelated implementation
- if there is no active version, enter harness mode but explain that the next step is to create or activate a version