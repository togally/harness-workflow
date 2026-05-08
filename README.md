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
- **Multi-platform** — works on Claude Code, Codex, Qoder, and kimicli

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

## Installation

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

Then initialize a repository:

```bash
cd your-project
harness install          # installs skill files for Claude Code / Codex / Qoder / kimicli
```

If you need to overwrite existing skill files (e.g., after a breaking update):

```bash
harness install --force  # force reinstall of all platform skills
```

---

## Core Commands

| Command | Description |
|---------|-------------|
| `harness status` | Show current requirement, stage, and runtime state |
| `harness validate` | Validate artifacts and run Python syntax checks for the current requirement |
| `harness requirement "<title>"` | Create a new requirement and enter requirement_review |
| `harness change "<title>"` | Create a new change within the current requirement |
| `harness next` | Advance to the next workflow stage |
| `harness next --execute` | Confirm execution (required to enter executing stage) |
| `harness regression "<issue>"` | Start a regression analysis flow (closing actions auto-create experience file) |
| `harness archive <req-id> [--folder <name>]` | Archive a completed requirement (only `done` status); in a Git repo, prompts to auto-commit |
| `harness rename requirement <old> <new>` | Rename a requirement |
| `harness rename change <old> <new>` | Rename a change |
| `harness suggest "<content>"` | Quickly jot down an idea without starting a full requirement flow |
| `harness suggest --list` | List all pending suggestions |
| `harness suggest --apply <id>` | Turn a suggestion into a formal requirement and enter requirement_review |
| `harness suggest --apply-all [--pack-title "..."]` | Pack all pending suggestions into a single requirement |
| `harness suggest --delete <id>` | Delete a suggestion |
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

### Capture Ideas with Suggestions

Not every idea needs a full requirement immediately. Use `harness suggest` to capture raw thoughts, then promote them when ready:

```bash
harness suggest "Add dark mode toggle to settings page"
harness suggest "Refactor auth middleware to support JWT refresh tokens"
harness suggest --list
harness suggest --apply sug-01                   # creates req-XX and enters requirement_review
harness suggest --apply-all                      # pack all pending suggestions into one requirement
harness suggest --apply-all --pack-title "X"     # pack with a custom requirement title
```

---

## Local Development

After modifying source code locally, you need to re-inject into the pipx environment for changes to take effect:

```bash
pipx inject harness-workflow . --force
```

---

## Where Detailed Rules Live

All workflow rules, roles, and constraints are stored under `.workflow/`. Key entry points:

- `WORKFLOW.md` — workflow entry point for agents
- `.workflow/context/index.md` — loading order and routing rules
- `.workflow/context/roles/<stage>.md` — per-stage role definitions (requirement-review, planning, executing, testing, acceptance, regression, done)
- `.workflow/context/experience/` — accumulated project lessons
- `.workflow/constraints/` — behavioral boundaries, risk scanning, and failure recovery paths
- `.workflow/flow/stages.md` — stage definitions and transition conditions
- `.workflow/tools/` — tool catalog, selection guide, and per-stage allowlists

> 💡 **Tip:** You don't need to memorize the directory tree. Start with `WORKFLOW.md` and `.workflow/context/index.md`; they will route you to the right role and constraint files automatically.

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

## Supported Platforms

| Platform | Entry Files |
|----------|-------------|
| Claude Code | `CLAUDE.md`, `.claude/commands/harness-*.md`, `.claude/skills/harness/` |
| Codex | `AGENTS.md`, `.codex/skills/harness/`, `.codex/skills/harness-*/` |
| Qoder | `.qoder/skills/harness/`, `.qoder/commands/harness-*.md`, `.qoder/rules/harness-workflow.md` |
| kimicli | `.kimi/skills/{command}/SKILL.md` (YAML frontmatter + Markdown) |

---

## Artifacts Repository

The `artifacts/` directory serves as a knowledge base for completed requirements:

- **`artifacts/requirements/`** — Auto-generated by `harness archive`. Each archived requirement produces a `{req-id}-{title}.md` summary doc covering business context, goals, scope, acceptance criteria, change list, and key design decisions. Useful for onboarding new team members.
  > **Note:** `harness archive` only processes requirements in `done` status. Requirements that haven't completed the full workflow cannot be archived.
- Other subdirectories (`sql/`, `api/`, etc.) are managed manually by the team.

## harness pad — 项目级承载层维护

往 `artifacts/project/` 加规则 / 经验 / 工具，命令封装"路径正确 + index 登记 + git stage"全套：

```bash
# 加规则（5 个 scope：coding / architecture / api / database / security）
harness pad rule coding "禁止-API-硬编码"

# 加经验（5 个 scope：roles / stage / regression / risk / tool）
harness pad experience stage "executing-虚报教训"

# 加工具（不分 scope）
harness pad tool "petmall-deployer"

# 列已有
harness pad list

# 无参数 → 交互引导
harness pad
```

落位规则（固定枚举，user 不能发明）：

| kind | 路径 |
|------|------|
| rule | `artifacts/project/constraints/{scope}/{slug}.md` |
| experience | `artifacts/project/experience/{scope}/{slug}.md` |
| tool | `artifacts/project/tools/{slug}.md` |

命令成功后会自动 `git add`；user 仅需 `git commit -m "..."`（按 stdout 提示）。

---

## Third-party Vendored Skills

harness-workflow bundles a vendored snapshot of **[gstack](https://github.com/garrytan/gstack)** — a YC-style engineering assist skill collection (MIT license, 46 skills). When you run `harness install --agent claude`, all gstack skills are automatically pushed to `~/.claude/skills/` so you can invoke any gstack skill directly in Claude Code without additional setup.

### Bundled Skills

| Skill | Purpose |
|-------|---------|
| `office-hours` | YC-style startup/project brainstorming with forcing questions |
| `investigate` | Deep technical investigation and root-cause analysis |
| `qa` | Quality assurance and test-case driven reviews |
| `review` | Code review with opinionated feedback |
| `codex` | Autonomous multi-step coding with a scratchpad |
| `plan-eng-review` | Engineering manager–mode plan review and architecture lock-in |
| `plan-ceo-review` | CEO-mode product review with strategic alignment check |
| `plan-design-review` | Design review for UI/UX decisions |
| `ship` | End-to-end ship workflow (build → test → deploy) |
| `canary` | Canary release and gradual rollout management |
| `land-and-deploy` | Landing and deployment pipeline helper |
| `retro` | Sprint retrospective facilitation |
| `browse` | Structured web browsing with scraping |
| `scrape` | Web scraping for data extraction |
| `design-consultation` | Design thinking consultation |
| `design-html` | Rapid HTML/CSS prototyping |
| `design-review` | Visual design review |
| `design-shotgun` | Multi-option design exploration |
| `devex-review` | Developer experience review |
| `autoplan` | Automatic planning from a spec or requirements |
| `benchmark` | Performance benchmarking |
| `benchmark-models` | LLM model benchmarking |
| `careful` | Careful, step-by-step execution with safety gates |
| `freeze` / `unfreeze` | Freeze/unfreeze repository state |
| `guard` | Guard rails and safety checks |
| `health` | Project health check |
| `learn` | Structured learning and knowledge capture |
| `make-pdf` | PDF generation from markdown |
| `pair-agent` | Pair-programming with a second agent |
| `context-save` / `context-restore` | Save and restore agent context |
| `gstack-upgrade` | Upgrade gstack to latest version |
| `setup-deploy` | Deployment setup wizard |
| `setup-gbrain` | gbrain integration setup |
| `setup-browser-cookies` | Browser cookie configuration |
| `sync-gbrain` | Sync with gbrain knowledge base |
| `document-release` | Release note documentation |
| `landing-report` | Landing page analysis report |
| `cso` | Chief strategy officer–mode strategic review |
| `open-gstack-browser` | Open gstack browser integration |
| `connect-chrome` | Connect to a Chrome DevTools Protocol instance |
| `plan-devex-review` | Developer experience plan review |
| `plan-tune` | Plan tuning and refinement |
| `qa-only` | QA-only mode without code changes |
| `skillify` | Convert a prompt into a reusable skill |

### Attribution

```
gstack — MIT License
Copyright (c) 2026 Garry Tan
https://github.com/garrytan/gstack

Vendored snapshot: commit c7aefc1 (2026-05-07)
Full license: src/harness_workflow/assets/gstack-skills/_shared/LICENSE-gstack
```

> The vendored copy includes only `SKILL.md` files and supporting `references/`/`scripts/` subdirectories, plus shared `bin/`, `agents/`, and `scripts/` runtime resources. Build artifacts, `node_modules`, `.git`, and `contrib/` are excluded.
>
> To re-vendor or upgrade: `scripts/vendor-gstack.sh --all <commit> --from-local <path>`
