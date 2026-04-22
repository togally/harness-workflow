# AGENTS.md

This repository uses the Harness workflow for agent collaboration.

## Hard Gate

Do not act until `WORKFLOW.md`, `.workflow/context/index.md`, and `.workflow/state/runtime.yaml` have been read.

If any of those files are missing, inconsistent, or unreadable, stop immediately and do not fall back to a legacy entrypoint.

## Entry

1. Read `WORKFLOW.md`.
2. Read `.workflow/context/index.md`.
3. Read `.workflow/state/runtime.yaml`.
4. **Immediately load the `harness-manager` role**: use the Skill tool to invoke `harness-install`, letting harness-manager take over routing.
5. Load the matching role, experience, and constraint files by following `.workflow/context/index.md`.
6. If the human is unhappy with a completed result, start `harness regression "<issue>"` before creating new work.
7. If `conversation_mode: harness`, stay inside the locked requirement and stage until the human explicitly exits.

## Main Entry

- `harness install`（已吸收原 update 的 CLI 刷新职责；req-33 / chg-01）
- `harness update`（触发 project-reporter 生成 `artifacts/main/project-overview.md`；CLI 同步职责请用 `harness install`；req-33 / chg-02）
- `harness status`
- `harness requirement "<title>"`
- `harness change "<title>"`
- `harness next`
- `harness regression "<issue>"`

If runtime state is missing or inconsistent, repair `.workflow/state/runtime.yaml` instead of improvising a parallel workflow; if required files are missing, stop immediately.
