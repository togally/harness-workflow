---
description: Run harness requirement and continue work inside the current Harness workflow state
argument-hint: "<title>"
---

This command maps to `harness requirement`.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.
If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

Before acting:

1. Read the root `WORKFLOW.md`
2. Read `.workflow/context/index.md`
3. Then read `.workflow/state/runtime.yaml`
4. Load any additional role / experience / constraint files by following `.workflow/context/index.md`
5. Prefer the root `AGENTS.md`
6. If `.kimi/skills/harness/SKILL.md`, `.qoder/skills/harness/SKILL.md` or `.claude/skills/harness/SKILL.md` exists, follow the main Harness skill

Execution rules:

- center the task around `harness requirement`
- do not bypass the workflow with manual requirement / change / plan / execution steps
- if workflow state is missing or inconsistent, handle by command type:
  - install/init/update/language/status are standalone commands; no current_requirement needed
  - other commands require current_requirement; if missing, stop and prompt user
- if compilation fails, startup fails, or human-provided external input is required, enter regression first
- if human input is required, fill the related change `regression/required-inputs.md` before asking for it

If the user adds more instruction, combine it with the current workflow state to decide the next step.

Focus:

- confirm there is an active version first; if not, guide the user to `harness version` or `harness active`
- after creating the requirement, fill in background, goal, scope, and acceptance boundaries first
- do not jump into implementation; discuss whether the requirement is correct
- once the requirement is approved, point to splitting changes or running `harness next`

---

## --fallback 标志（req-56）

`harness requirement "<title>"` 默认行为已与 gstack `/office-hours` 强映射打通：analyst 进入 Step A1.5 后会通过 batched-report 让你在主对话执行 `/office-hours`，完成后把 design doc path 回传，由 analyst 按 adapter SOP 重组为 requirement.md。

如需跳过 office-hours 走原生 analyst 手工 SOP（小需求 / 已想清楚 / 不想多走一层），追加 `--fallback`：

```
harness requirement "<title>" --fallback
```

CLI 会把 `office_hours_mode: fallback` 写到 `.workflow/state/requirements/{req-id}-{slug}.yaml`，analyst 据此跳过 path α 直接 Step A2。

如果你用的是非 Claude Code agent（gstack /office-hours 不可用），CLI 检测 `gstack_status.agent_kind_compatible=false` 时会自动 fallback + stdout 警告 `[gstack] agent 不兼容，本 req 自动 fallback 模式`。

无论走 fallback 还是 office-hours 路径，最终 requirement.md 必须落到 `.workflow/flow/requirements/{req-id}-{slug}/requirement.md`，含 frontmatter 5 字段（id / title / created_at / operation_type / stage）+ 4 章节（Goal / Scope / Acceptance Criteria / Split Rules），统一通过 `harness validate --human-docs` + `harness validate --contract artifact-placement` 双绿。
