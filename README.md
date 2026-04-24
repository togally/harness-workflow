# harness-workflow

> 📖 [中文文档](README.zh.md)

**Structured AI workflow system** for AI-assisted software development. harness-workflow gives AI agents a document-driven, role-separated, stage-gated operating model so your work is traceable, repeatable, and auditable — not just "good vibes in a big context window."

Core philosophy: **govern AI development, don't just prompt it.**

Most AI coding tools give you one large context window and hope for the best. harness-workflow adds structure:

---

## §1 What it is and what problem it solves

- **Stage-gated workflow** — requirement review → planning → executing → testing → acceptance → done
- **Role separation** — each stage uses a dedicated agent role; the producer and evaluator are always different instances
- **Persistent state** — requirements and changes survive context resets via YAML + Markdown files in `.workflow/`
- **Experience accumulation** — lessons from every project are captured and fed back into future sessions
- **Multi-platform** — Claude Code, Codex, Qoder, and kimicli

---

## §2 Installation

**Standard users** — install from GitHub:

```bash
pipx install git+https://github.com/togally/harness-workflow.git
```

**Upgrade to the latest released version** — a `pipx`-installed binary is a snapshot and does **not** auto-update when upstream changes:

```bash
pipx reinstall harness-workflow
# or equivalently:
pipx upgrade harness-workflow
```

**Developers / local source editing** — install in editable mode so source changes take effect immediately:

```bash
pipx install -e /path/to/harness-workflow
# git pull inside the repo is all you need to pick up new changes
```

**Initialize a project** — run this inside any repo you want to manage with harness:

```bash
cd your-project
harness install          # sets up .workflow/ scaffold + skill files for all platforms
harness install --force  # force-overwrite existing skill files after a breaking update
```

`harness install` is idempotent — safe to run repeatedly. It initializes the scaffold, syncs skill files, migrates legacy state, and writes the experience index and project profile.

> **Refreshing templates:** to re-sync skill files and managed files in an existing project, run `harness install` again (not `harness update` — see §3).

---

## §3 Commands

| Command | What it does |
|---------|--------------|
| `harness install [--force]` | Initialize / refresh scaffold and skill files (`--force` overwrites existing) |
| `harness status` | Show current requirement, stage, and runtime state |
| `harness validate` | Check artifact completeness for the current requirement |
| `harness requirement "<title>"` | Create a requirement and enter review stage |
| `harness change "<title>"` | Create a change within the current requirement |
| `harness next` | Advance to the next stage |
| `harness next --execute` | Confirm execution (required to enter the executing stage) |
| `harness ff` | Fast-forward: AI auto-advances through all remaining stages |
| `harness suggest "<content>"` | Capture an idea without starting a full requirement |
| `harness suggest --list` | List all pending suggestions |
| `harness suggest --apply <id>` | Promote a suggestion into a formal requirement |
| `harness suggest --apply-all [--pack-title "..."]` | Pack all pending suggestions into one requirement |
| `harness suggest --delete <id>` | Delete a suggestion |
| `harness regression "<issue>"` | Start a regression diagnosis flow; closing actions auto-create an experience file |
| `harness regression --confirm` | Confirmed real issue — proceed with fix |
| `harness regression --reject` | False alarm — return to previous stage |
| `harness regression --change / --requirement "<title>"` | Convert diagnosis result into a new change or requirement |
| `harness archive <req-id> [--folder <name>]` | Archive a completed requirement (only `done` status) |
| `harness rename requirement/change <old> <new>` | Rename a requirement or change |
| `harness feedback` | Export usage event summary |

### `harness update` — what it actually does

`harness update` is **not** a CLI upgrade command. Do not use it to upgrade the harness tool itself (use `pipx reinstall harness-workflow` for that).

| Invocation | Behavior |
|------------|----------|
| `harness update` (no flag) | Prints a short guide, then exits. To generate a project status report, say **"生成项目现状报告"** inside an agent session. |
| `harness update --check` | Drift preview — shows which managed files differ from templates |
| `harness update --scan` | Project adaptation scan — detects tech stack and directory layout |

---

## §4 Usage scenarios

### Scenario A: Deliver a new requirement end-to-end

```bash
harness install                          # first-time project setup
harness requirement "Online Health API"  # enter requirement review
# discuss and confirm scope with the AI
harness next                             # advance to planning
# review the change breakdown and plan
harness next --execute                   # confirm and start execution
# AI implements the changes
harness next                             # → testing
harness next                             # → acceptance
harness next                             # → done
harness archive req-01                   # archive the completed requirement
```

Flow: requirement review → planning → executing → testing → acceptance → done. All four platforms (Claude Code, Codex, Qoder, kimicli) share the same `.workflow/` state.

### Scenario B: Capture a quick idea, decide later

```bash
harness suggest "Add dark mode toggle to settings page"
harness suggest "Refactor auth middleware for JWT refresh"
harness suggest --list                         # review the backlog
harness suggest --apply sug-01                 # promote to a formal requirement
harness suggest --apply-all --pack-title "UI polish sprint"  # pack all into one req
```

Suggestions sit in a lightweight pool — no stage overhead until you decide to act.

### Scenario C: Something went wrong — diagnose and fix

```bash
harness regression "Login fails after token refresh"
# AI diagnoses root cause and writes diagnosis.md
harness regression --confirm              # confirmed real issue → enters fixing flow
# or
harness regression --change "Fix token refresh edge case"   # creates a new change
# or
harness regression --reject               # false alarm, return to previous stage
```

Regression can be triggered from any stage. Closing a regression automatically captures an experience file for future sessions.

### Scenario D: Multi-platform setup

`harness install` writes skill files for all four platforms at once. Run `harness install --force` after a CLI upgrade to keep all platform skill files current.
