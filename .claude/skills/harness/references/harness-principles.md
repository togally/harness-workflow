# Harness Initialization Principles

## Goal

Make a repository easier for agents to understand, navigate, and operate safely across sessions.

## Principles

### Use a short root guide

Keep `AGENTS.md` small and route into stable documents instead of duplicating the full project handbook at the root.

### Separate durable memory from working memory

- Durable memory belongs in `workflow/memory/`
- Change-specific working memory belongs in `workflow/changes/active/<change-id>/session-memory.md`

### Keep context layered

Use different directories for:

- team-wide rules,
- current project facts,
- experience and common errors,
- active change workspaces,
- plans and decisions.

### Prefer explicit loading rules

Agents should know:

- what to read first,
- what to read only on demand,
- what is authoritative,
- what is only advisory.

### Favor incremental adoption

If a repository already has useful documents, bridge and reference them first. Do not discard them just to make the tree look cleaner.
