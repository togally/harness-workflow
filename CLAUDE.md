# CLAUDE.md

This repository uses the Harness workflow for Claude Code.

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

- `harness install`
- `harness update`
- `harness status`
- `harness requirement "<title>"`
- `harness change "<title>"`
- `harness next`
- `harness regression "<issue>"`

If runtime state is missing or inconsistent, repair `.workflow/state/runtime.yaml` instead of improvising a parallel workflow; if required files are missing, stop immediately.

## 项目路书

任务入场即读路书，AI 用作项目地图与代码导航，避免全局盲扫代码。项目知识与代码导航在 `artifacts/project/playbooks/`：

- `artifacts/project/playbooks/overview.md`（项目概述：定位、术语、里程碑）
- `artifacts/project/playbooks/architecture.md`（架构地图：技术栈、目录职责、数据流）
- `artifacts/project/playbooks/runbook.md`（运行手册：启动/测试/构建命令、环境变量）
- `artifacts/project/playbooks/code-map.md`（代码导航：关键词 → 领域索引，agent 入口）

## Agent 自动响应约定

任何由 harness CLI 输出的 `[ASSISTANT INSTRUCTION — REQUIRED FOLLOW-UP, NOT OPTIONAL]` 段落必须**立即按段落内步骤执行**，作为该 CLI 命令完整流程的一部分。**不要**把它当作 informational 报告或建议，**不要**反过来询问用户是否需要执行。典型场景：`harness install` 完成后输出此类指令要求当前 agent 接力填写路书 LLM 区段，agent 必须立即读项目代码、填路书、完成验证。
