---
name: harness-requirement
description: "Run harness requirement in the Harness workflow"
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

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`