---
name: harness
description: "Use when Codex, Claude Code, or Qoder needs to operate a repository with a Harness Engineering workflow: initialize the repo, switch language profiles, create version containers, place requirements and changes under the active version, prepare model-executable plans, and enforce thin root guides plus docs-based execution rules."
---

# Harness

## Overview

Operate a repository through explicit work artifacts instead of ad-hoc chat.
Use this skill to initialize a harness-enabled repository and then drive work through `language -> version -> requirement/change -> plan -> execution`, with regression diagnosis available when completed results need to be challenged, while capturing lessons during execution so the next session starts smarter.

## Command Model

Use these subcommands conceptually:

1. `harness init`
   Initialize the repository structure, root guides, docs entrypoints, templates, and lint checks.
2. `harness language <english|cn>`
   Switch the repository language profile for generated templates and localized artifact directories.
3. `harness version <name>`
   Create or switch the active version container.
4. `harness active <name>`
   Explicitly repair or switch the active version route when runtime state is missing or inconsistent.
5. `harness requirement <title>`
   Create a requirement inside the active version, then use `brainstorming` with the developer to refine it and split it into multiple `change` units.
6. `harness change <title>`
   Create one concrete, independently deliverable change.
7. `harness plan <change>`
   Use `writing-plans` to turn one change into a model-executable implementation plan.
8. `harness rename <kind> <old> <new>`
   Rename a version, requirement, or change while keeping metadata aligned.
9. `harness archive <requirement>`
   Move one completed requirement and its linked changes into the current version archive.
10. `harness regression <issue>`
   Start a regression diagnosis flow, confirm whether a complaint is a real problem, and only then convert it into a new requirement update or change.

Default rule: do not go from large requirement directly into implementation. Split into `change` first.
Regression rule: do not go from dissatisfaction directly into rework. Confirm the problem first, then convert it into formal work.

## Command Resolution

Prefer the global `harness` CLI when it is available.

```bash
harness install
harness version "v1.0.0"
harness requirement "Online Health Service"
```

If the global CLI is unavailable, fall back to the installed project-local skill script:

- Codex: `.codex/skills/harness/scripts/harness.py`
- Claude Code: `.claude/skills/harness/scripts/harness.py`
- Qoder: `.qoder/skills/harness/scripts/harness.py`

For Qoder, prefer the project command family such as `/harness`, `/harness-requirement`, `/harness-change`, and `/harness-plan` when they are available. Back them with `.qoder/commands/harness-*.md`, then route into the same shared Harness skill and docs workflow.
For Claude Code, generate the same command family under `.claude/commands/harness-*.md`.
For Codex, expose the same command family as thin `.codex/skills/harness-*` wrappers around the main Harness skill.

Do not assume there is a repository-local `scripts/harness.py` in the target project root.
If neither the global CLI nor the installed local skill script exists, stop and report the missing harness installation instead of hand-creating the workflow structure.

If workflow state is missing or inconsistent, stop immediately instead of improvising a parallel workflow by hand. Typical blockers include:

- missing `current_version`
- disagreement between `workflow-runtime.yaml` and harness config
- missing version `meta.yaml`
- a blocked stage with no confirmed next action

In those cases, direct the developer to repair the route with `harness active "<version>"` or restore the missing workflow files before continuing.
If the developer wants to rename folders, prefer `harness rename` over manual moves. If manual folder renames already happened, run `harness update` to repair identifier drift before continuing.

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
Before each stage starts a concrete task, re-index relevant experience. After each stage completes, capture new lessons and fuse mature experience back into the current requirement, change, plan, or execution approach when useful.
Regression history should be kept in its own regression directory and documents. Do not keep resolved regressions occupying the main version workflow state longer than necessary.

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
harness install --root /path/to/repo
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
harness version "v1.0.0" --root /path/to/repo
```

If the active route is broken, repair it with:

```bash
harness active "v1.0.0" --root /path/to/repo
```

Enter harness conversation mode explicitly with:

```bash
harness enter --root /path/to/repo
```

Exit harness conversation mode with:

```bash
harness exit --root /path/to/repo
```

Optionally switch language:

```bash
harness language cn --root /path/to/repo
```

Create a requirement workspace with:

```bash
harness requirement "Online Health Service" --root /path/to/repo
```

Then:

1. Use `brainstorming` to refine the requirement with the developer.
2. Write the result into the active version requirement container.
3. Split the requirement into multiple `change` units in `changes.md`.
4. Even if the developer provides an implementation-oriented prompt at this stage, treat it as requirement discussion input only. Do not implement code during `requirement_review`.

Use requirement workspaces for themes, not for single-file tweaks.
All `harness ...` commands auto-enter harness conversation mode. Once in harness mode, keep the conversation inside the current workflow node until the developer explicitly calls `harness exit`.

## Harness Change

Create one concrete change with:

```bash
harness change "Online Booking" --root /path/to/repo [--requirement <requirement-title-or-id>]
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
Each completed `change` must include `mvn compile`. If compilation fails, start `harness regression "<issue>"`. If user-provided inputs are needed, fill `regression/required-inputs.md` first and only then ask the human to complete it.
If the needed debug information is already available on the local machine, collect it first instead of asking the human to inspect it manually.

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
harness version "v1.0.0" --root /path/to/repo
```

This should create `requirements`, `changes`, and `plans` containers under the active version.
Use versions as the main work container, while `docs/context/` remains repository-level knowledge.
When a requirement is complete, record successful project startup validation in its `completion.md`. If startup fails, enter regression first.
Local startup logs, compiler output, and stack traces should be collected by the agent before it asks the human for help.
`harness enter` should lock the conversation to the current version and workflow node. `harness exit` should release that lock without mutating the current stage.

## Root Guides

Keep `AGENTS.md` and `CLAUDE.md` thin.
They should route the agent into `docs/` and never become full business handbooks.
For Qoder, keep `.qoder/commands/harness-*.md` and `.qoder/rules/harness-workflow.md` equally thin and route them to the same shared `docs/context/rules/*` and version state files.
For Claude Code, keep `.claude/commands/harness-*.md` thin in the same way.
For Codex, keep `.codex/skills/harness-*` as thin wrappers instead of copying business rules into many separate skills.

Detailed rules belong in:

- `docs/context/rules/agent-workflow.md`
- `docs/context/hooks/README.md`
- `docs/context/rules/risk-rules.md`
- `docs/context/project/project-overview.md`
- `docs/context/team/development-standards.md`

Root guides should also remind the agent to read indexed experience before working and to update working memory when new lessons appear.

## Validate

Validate the repository after changes:

```bash
python3 tools/lint_harness_repo.py --root /path/to/repo --strict-agents --strict-claude
```

Validate the skill itself:

```bash
python3 /Users/jiazhiwei/.codex/skills/.system/skill-creator/scripts/quick_validate.py /path/to/harness
```

If lint fails, fix the missing files or broken routing before claiming the harness workflow is ready.
