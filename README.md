# harness-workflow

> 📖 [中文文档](README.zh.md)

**Structured AI workflow system** for requirement management, change tracking, multi-stage quality gates, and experience accumulation in AI-assisted software development.

Core philosophy: **govern AI development, don't just prompt it.** Document-driven, role-separated, and structurally constrained — so AI agents operate within clear boundaries, producing traceable, auditable results.

---

## Why harness-workflow?

Most AI coding tools leave you with one big context window and hope. harness-workflow gives you:

- **Stage-gated workflow** — requirements → changes → planning → execution → testing → acceptance → done
- **Role separation** — each stage uses a dedicated agent role (analyst, architect, engineer, tester, auditor)
- **Persistent state** — requirements and changes survive context window resets via YAML + Markdown files
- **Experience accumulation** — lessons from each project are captured and reused in future sessions
- **Multi-platform** — works on Claude Code, Codex, and Qoder

---

## Six-Layer Architecture

```
.workflow/
├── context/        ← Layer 1: Roles, experience, project background, team standards
├── tools/          ← Layer 2: Tool catalog, selection guide, per-stage allowlists
├── flow/           ← Layer 3: Stage definitions, requirement docs, change plans
├── state/          ← Layer 4: Runtime state, requirement progress, session memory
├── evaluation/     ← Layer 5: Testing rules, acceptance criteria, regression diagnosis
└── constraints/    ← Layer 6: Behavioral boundaries, risk scanning, failure recovery
```

### Stage Flow

```
requirement_review
        ↓
  changes_review
        ↓
   plan_review
        ↓
ready_for_execution
        ↓
    executing
        ↓
     testing
        ↓
    acceptance
        ↓
      done
```

Each stage has a dedicated role file in `.workflow/context/roles/` that constrains behavior, tool access, and exit conditions.

---

## Installation

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

Then initialize a repository:

```bash
cd your-project
harness install          # installs skill files for Claude Code / Codex / Qoder
```

---

## Core Commands

| Command | Description |
|---------|-------------|
| `harness status` | Show current requirement, stage, and runtime state |
| `harness requirement "<title>"` | Create a new requirement and enter requirement_review |
| `harness change "<title>"` | Create a new change within the current requirement |
| `harness next` | Advance to the next workflow stage |
| `harness next --execute` | Confirm execution (required to enter executing stage) |
| `harness regression "<issue>"` | Start a regression analysis flow |
| `harness archive <req-id> [--folder <name>]` | Archive a completed requirement |
| `harness rename requirement <old> <new>` | Rename a requirement |
| `harness rename change <old> <new>` | Rename a change |
| `harness ff` | Fast-forward to ready_for_execution |
| `harness update` | Refresh harness-managed files in the repository |
| `harness feedback` | Export usage event summary |

### Quick Start

```bash
harness install
harness requirement "Online Health Service"
# ... discuss and confirm the requirement with the AI ...
harness next
# ... split into changes, review plans ...
harness next --execute
# ... implementation ...
harness next          # → testing
harness next          # → acceptance
harness next          # → done
```

---

## Practical Principles

1. **Don't compress when context is full** — start a new agent and hand off via `session-memory.md`
2. **Separate agents per stage** — producer and evaluator must be different instances
3. **Review beyond the code** — operate the UI, verify interactions, check results
4. **Independent feedback loops** — role separation is the prerequisite for effective iteration
5. **Attribute problems structurally** — when an agent fails, look inward at the constraints
6. **Thin entry points** — directory indexes keep context lean; details surface on demand
7. **Sustainable autonomy** — the goal is a self-running system, not perpetual hand-holding

---

## Supported Platforms

| Platform | Entry Files |
|----------|-------------|
| Claude Code | `CLAUDE.md`, `.claude/commands/harness-*.md`, `.claude/skills/harness/` |
| Codex | `AGENTS.md`, `.codex/skills/harness/`, `.codex/skills/harness-*/` |
| Qoder | `.qoder/skills/harness/`, `.qoder/commands/harness-*.md`, `.qoder/rules/harness-workflow.md` |

---

## Where Detailed Rules Live

- `WORKFLOW.md` — workflow entry point for agents
- `.workflow/context/index.md` — loading order and routing rules
- `.workflow/context/roles/<stage>.md` — per-stage role definitions
- `.workflow/context/experience/` — accumulated project lessons
- `.workflow/constraints/` — behavioral boundaries and risk rules
- `.workflow/flow/stages.md` — stage transition conditions

---

## Repository Structure

```
.workflow/
├── context/
│   ├── index.md              # Loading order and routing rules
│   ├── roles/                # Stage-specific role definitions
│   ├── experience/           # Experience index and lesson files
│   ├── project/              # Project overview and background
│   └── team/                 # Team development standards
├── tools/
│   ├── index.md              # Tool system overview
│   ├── stage-tools.md        # Per-stage tool allowlists
│   ├── selection-guide.md    # Tool selection guide
│   └── catalog/              # Individual tool documentation
├── flow/
│   ├── requirements/         # Active requirement workspaces
│   ├── archive/              # Archived requirements (created on demand)
│   └── stages.md             # Stage transition rules
├── state/
│   ├── runtime.yaml          # Global runtime state
│   ├── requirements/         # Per-requirement state files
│   └── sessions/             # Session memory files
├── evaluation/               # Testing and acceptance rules
└── constraints/              # Behavioral boundaries and recovery paths
```
