---
name: harness-change
description: "Run harness change in the Harness workflow"
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

- decide whether this change belongs to a requirement or stands alone
- after creating the change, fill in intent, impact scope, risk points, and acceptance method first
- remind the user that every completed change must include `mvn compile`
- once the change is clear, point to `harness plan` or `harness next`