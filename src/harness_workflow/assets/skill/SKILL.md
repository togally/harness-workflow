---
name: harness
description: "Use when Codex needs to operate a repository with a Harness Engineering workflow: initialize the repo, switch language profiles, create version containers, place requirements and changes under the active version, prepare model-executable plans, and enforce AGENTS.md or CLAUDE.md routing plus docs-based execution rules."
---

# Harness

## Overview

Operate a repository through explicit work artifacts instead of ad-hoc chat.
Use this skill to initialize a harness-enabled repository and then drive work through `language -> version -> requirement/change -> plan -> execution`, while capturing lessons during execution so the next session starts smarter.

## Command Model

Use these subcommands conceptually:

1. `harness init`
   Initialize the repository structure, root guides, docs entrypoints, templates, and lint checks.
2. `harness language <english|cn>`
   Switch the repository language profile for generated templates and localized artifact directories.
3. `harness version <name>`
   Create or switch the active version container.
4. `harness requirement <title>`
   Create a requirement inside the active version, then use `brainstorming` with the developer to refine it and split it into multiple `change` units.
5. `harness change <title>`
   Create one concrete, independently deliverable change.
6. `harness plan <change>`
   Use `writing-plans` to turn one change into a model-executable implementation plan.

Default rule: do not go from large requirement directly into implementation. Split into `change` first.

## Built-In Lesson Capture

Harness includes experience accumulation by default. Do not treat this as a separate workflow.

Capture lessons in these moments:

- when the developer corrects the agent,
- when a technical constraint or hidden rule is discovered,
- when a path fails and should not be retried blindly,
- when a change is finishing and reusable lessons should be promoted.

Default write locations:

- current-task notes and failed paths: `docs/versions/active/<version-id>/<changes-dir>/<change-id>/session-memory.md`
- reusable indexed lessons: `docs/context/experience/`

Use `session-memory.md` as the first landing zone. Promote only validated lessons into indexed experience.

## Trigger Hints

Prefer this skill when the user is asking for any of these actions:

- initialize a repository-wide harness workflow
- create or refine a requirement
- split a requirement into multiple changes
- create one concrete change
- prepare a change plan before implementation
- create or switch an active version
- switch repository language between English and Chinese

Typical user wording includes:

- “新建需求”
- “拆成几个功能点”
- “创建 change”
- “给这个 change 做计划”
- “切到中文模板”
- “切到某个版本”
- “初始化 harness 仓库”

## Harness Init

Initialize the repository with:

```bash
python3 scripts/harness.py init --root /path/to/repo --write-agents --write-claude
```

This should create:

- thin `AGENTS.md` and `CLAUDE.md`
- `docs/context/`, `docs/memory/`, `docs/versions/`, and reusable `docs/templates/`
- templates for requirements, changes, plans, acceptance, and session memory
- repository lint helper
- repository config at `.codex/harness/config.json`

For repositories that already have `doc/`, bridge legacy documents instead of forcing an immediate rename.

## Harness Requirement

Before creating requirements or changes, create or switch a version:

```bash
python3 scripts/harness.py version "v1.0.0" --root /path/to/repo
```

Optionally switch language:

```bash
python3 scripts/harness.py language cn --root /path/to/repo
```

Create a requirement workspace with:

```bash
python3 scripts/harness.py requirement "Online Health Service" --root /path/to/repo
```

Then:

1. Use `brainstorming` to refine the requirement with the developer.
2. Write the result into the active version requirement container.
3. Split the requirement into multiple `change` units in `changes.md`.

Use requirement workspaces for themes, not for single-file tweaks.

## Harness Change

Create one concrete change with:

```bash
python3 scripts/harness.py change "Online Booking" --root /path/to/repo [--requirement <requirement-title-or-id>]
```

This creates a change workspace containing:

- `change.md`
- `design.md`
- `plan.md`
- `acceptance.md`
- `session-memory.md`
- `meta.yaml`

If the change belongs to a requirement, link it from that requirement's `changes.md`.
If not, it can stand alone inside the active version.

Each `change` should be independently plannable and independently verifiable.
Each `change` should also accumulate execution knowledge in `session-memory.md`, including what did not work.

## Harness Plan

Before implementation, use `writing-plans` for the selected change.

The plan must:

- live with the change or clearly point to it,
- include model-executable development steps,
- include explicit verification steps,
- avoid skipping directly from design to coding.

Default execution rule:

- each implementation step should have a matching verification step,
- each work step should be suitable for one subagent or one isolated execution unit,
- development and testing are separate steps unless the step is truly trivial.

For non-trivial execution, use `subagent-driven-development` or `executing-plans`.

## Harness Version

Create or switch an active version container with:

```bash
python3 scripts/harness.py version "v1.0.0" --root /path/to/repo
```

This should create `requirements`, `changes`, and `plans` containers under the active version.
Use versions as the main work container, while `docs/context/` remains repository-level knowledge.

## Root Guides

Keep `AGENTS.md` and `CLAUDE.md` thin.
They should route the agent into `docs/` and never become full business handbooks.

Detailed rules belong in:

- `docs/context/rules/agent-workflow.md`
- `docs/context/rules/risk-rules.md`
- `docs/context/project/project-overview.md`
- `docs/context/team/development-standards.md`

Root guides should also remind the agent to read indexed experience before working and to update working memory when new lessons appear.

## Validate

Validate the repository after changes:

```bash
python3 scripts/lint_harness_repo.py --root /path/to/repo --strict-agents --strict-claude
```

Validate the skill itself:

```bash
python3 /Users/jiazhiwei/.codex/skills/.system/skill-creator/scripts/quick_validate.py /path/to/harness
```

If lint fails, fix the missing files or broken routing before claiming the harness workflow is ready.
