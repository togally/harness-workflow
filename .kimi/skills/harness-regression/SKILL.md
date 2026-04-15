---
name: harness-regression
description: "Run harness regression in the Harness workflow"
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

- do not jump straight into rework; confirm whether it is a real problem first
- use locally available logs, compile output, and test failures before asking the human
- if human-provided external input is still needed, fill `regression/required-inputs.md` first
- only after confirmation should the regression become a new requirement update or change