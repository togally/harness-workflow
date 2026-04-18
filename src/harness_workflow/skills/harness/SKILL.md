---
name: harness
description: "Run harness in the Harness workflow. Use when operating a repository with the Harness workflow rooted at WORKFLOW.md and .workflow/state/runtime.yaml."
---

# Harness Workflow

## Overview

Harness is a structured workflow system for managing software development tasks through a series of stages: requirement review, planning, execution, testing, acceptance, and done.

## Hard Gate

Do not act until these three files have been read in order:
1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`

## Available Commands

| Command | Description |
|---------|-------------|
| `harness enter` | Enter harness workflow mode |
| `harness exit` | Exit harness workflow mode |
| `harness status` | Show current workflow status |
| `harness next` | Advance to next stage |
| `harness ff` | Fast-forward to next stage (ff mode) |
| `harness requirement <title>` | Create a new requirement |
| `harness change <title>` | Create a new change |
| `harness bugfix <title>` | Create a bugfix |
| `harness archive [req-id]` | Archive a completed requirement |
| `harness suggest` | Manage suggestions |
| `harness regression` | Start regression flow |
| `harness install` | Install harness skill to agent |
| `harness update` | Update harness skill for project |

## Role System

Harness uses a role-based system:

- **Technical Director**: Orchestrates the entire workflow
- **Requirement Analyst**: Clarifies user intent
- **Architect**: Splits requirements into changes
- **Developer**: Executes changes
- **Test Engineer**: Designs and executes tests
- **Acceptance**: Validates against requirements
- **Regression**: Diagnoses issues
- **harness-manager**: Manages skill installation and updates

## Stage Flow

```
requirement_review → planning → executing → testing → acceptance → done
                        ↓
                  regression (when needed)
```

## Key Files

- `.workflow/state/runtime.yaml` - Current workflow state
- `.workflow/context/roles/` - Role definitions
- `.workflow/flow/suggestions/` - Pending suggestions
- `.workflow/state/requirements/` - Requirement states
