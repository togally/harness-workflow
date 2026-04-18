---
name: harness
description: "Run harness in the Harness workflow. Use when operating a repository with the Harness workflow rooted at WORKFLOW.md and .workflow/state/runtime.yaml."
---

# Harness Workflow

## Overview

Harness is a structured workflow system for managing software development tasks through a series of stages. All harness commands are routed through the **harness-manager** role, which serves as the command guiding center.

## Hard Gate

Do not act until these three files have been read in order:
1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`

## Command Guiding Center (harness-manager)

The harness-manager role is the unified entry point for all harness commands. It:

1. **Command Understanding Layer**: Parses `harness <command>` intent into structured actions
2. **Role Scheduling Layer**: Dispatches to appropriate subagents based on command category
3. **Project Insight Layer**: Scans project characteristics for adaptation
4. **Tools Integration**: Delegates to toolsManager for tool recommendations

## Available Commands

### Installation & Update Commands

| Command | Description |
|---------|-------------|
| `harness install` | Initialize repository and install harness skill |
| `harness install --agent <agent>` | Install harness skill to specific agent (kimi/claude/codex/qoder) |
| `harness update` | Refresh harness-managed files in repository |
| `harness update --check` | Show what would change without writing |
| `harness update --scan` | Scan project and generate adaptation report |
| `harness language <english\|cn>` | Set repository language profile |

### Session Control Commands

| Command | Description |
|---------|-------------|
| `harness enter [req-id]` | Enter harness workflow mode at current version |
| `harness exit` | Exit harness workflow mode |
| `harness status` | Show current workflow status |
| `harness validate` | Validate current requirement's artifacts |

### Workflow Progression Commands

| Command | Description |
|---------|-------------|
| `harness next [--execute]` | Advance to next stage |
| `harness ff` | Fast-forward to ready_for_execution (mode A only) |

### Artifact Management Commands

| Command | Description |
|---------|-------------|
| `harness requirement <title>` | Create a new requirement |
| `harness change <title>` | Create a new change |
| `harness bugfix <title>` | Create a bugfix and enter regression |
| `harness archive [req-id]` | Archive a completed requirement |
| `harness rename <kind> <old> <new>` | Rename a requirement or change |

### Auxiliary Commands

| Command | Description |
|---------|-------------|
| `harness suggest [content]` | Create, list, apply, or delete suggestions |
| `harness tool-search <keywords...>` | Search local tool index |
| `harness tool-rate <tool-id> <rating>` | Rate a tool (1-5) |
| `harness regression [issue]` | Start or advance regression diagnosis |
| `harness feedback [--reset]` | Export feedback summary |

## Command Categories

### Category 1: Installation & Update → harness-manager executes directly

These commands are handled by harness-manager:
- `harness install` / `harness install --agent <agent>`
- `harness update` / `harness update --check` / `harness update --scan`
- `harness language`

### Category 2: Session Control → technical-director executes

These commands control workflow conversation mode:
- `harness enter` / `harness exit`
- `harness status` / `harness validate`

### Category 3: Workflow Progression → technical-director executes

These commands advance stage flow:
- `harness next` / `harness ff`

### Category 4: Artifact Management → stage roles execute

These commands create and manage requirements/changes:
- `harness requirement` → requirement-review role
- `harness change` → planning role
- `harness bugfix` → regression role
- `harness archive` / `harness rename` → direct execution

### Category 5: Auxiliary Functions → respective roles execute

- `harness suggest` → suggestion pool management
- `harness tool-search` → toolsManager delegates
- `harness tool-rate` → direct execution
- `harness regression` → regression role
- `harness feedback` → direct execution

## Role System

Harness uses a role-based system:

- **Technical Director**: Orchestrates the entire workflow
- **Requirement Analyst**: Clarifies user intent
- **Architect**: Splits requirements into changes
- **Developer**: Executes changes
- **Test Engineer**: Designs and executes tests
- **Acceptance**: Validates against requirements
- **Regression**: Diagnoses issues
- **harness-manager**: Command guiding center for all harness commands
- **toolsManager**: Tool search and recommendation

## Stage Flow

```
requirement_review
      ↓ harness next
   planning
      ↓ harness next
   executing
      ↓ harness next
   testing
      ↓ harness next
  acceptance
      ↓ harness next
    done

任意阶段 ──harness regression──→ regression
                                      ↓
                         ┌────────────┴────────────┐
                   需求/设计问题              实现/测试问题
                         ↓                          ↓
               requirement_review               testing
```

## Key Files

- `.workflow/state/runtime.yaml` - Current workflow state
- `.workflow/context/roles/` - Role definitions
- `.workflow/flow/suggestions/` - Pending suggestions
- `.workflow/state/requirements/` - Requirement states
- `.workflow/tools/index/keywords.yaml` - Tool keyword index
- `.workflow/tools/ratings.yaml` - Tool ratings

## Execution Protocol

1. **Parse**: User invokes `harness <command>`
2. **Understand**: harness-manager parses command intent
3. **Schedule**: Determine execution role (self or subagent)
4. **Execute**: Run command or dispatch to subagent
5. **Log**: Record action to `.workflow/state/action-log.md`
6. **Report**: Report results to user

## Project Insight

Before executing certain commands, harness-manager may scan:

- **Tech Stack**: package.json, go.mod, pom.xml, Cargo.toml, pyproject.toml
- **Directory Structure**: src/, tests/, docs/, .github/, scripts/
- **Harness Files**: .workflow/, .codex/skills/harness/, .claude/skills/harness/
- **Norm Files**: development-standards.md, CLAUDE.md, AGENTS.md
