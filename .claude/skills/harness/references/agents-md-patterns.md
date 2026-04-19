# AGENTS.md Patterns

## Root File Responsibilities

Use `AGENTS.md` for routing and priority, not for every detail.

Recommended sections:

1. Repository summary
2. Key entry files
3. Required reading order
4. Common validation commands
5. Pointers into detailed rule files

## Minimum Routing Rules

At minimum, `AGENTS.md` should tell the agent to:

1. Read `.workflow/memory/constitution.md` before analysis or design work
2. Read `.workflow/context/experience/index.md` before analysis, design, implementation, or self-check
3. Load only matching experience files instead of the full experience tree
4. Use `.workflow/context/rules/agent-workflow.md` for the detailed workflow

## Anti-Patterns

Avoid these patterns:

- putting the entire engineering handbook into `AGENTS.md`
- duplicating the same rules across `AGENTS.md`, `constitution.md`, and workflow documents
- making `AGENTS.md` the only source of truth
