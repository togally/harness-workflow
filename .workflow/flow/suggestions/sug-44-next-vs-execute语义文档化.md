---
id: sug-44
title: `harness next` vs `harness next --execute` 的 CLI help / 文档明示差异
status: pending
created_at: "2026-04-22"
priority: medium
---

# 背景

req-32（动态上下文生成：update 扫描项目描述 + CTO 任务级上下文注入）发现：

- `harness next`：仅推进 stage，不打 briefing，不落 task-context 快照
- `harness next --execute`：推进 stage + 打 JSON fence briefing（含 task_context_index + task_context_index_file）+ 落快照到 `.workflow/state/sessions/{req-id}/task-context/`

当前 `harness next --help` 对 `--execute` 的描述过于简略（通常只写 "advance and execute"）。主 agent 第一次碰会混淆"已经推进了吗？briefing 去哪了？"

# 建议

- 扩展 `--execute` help 文案：`"Advance to next stage AND emit subagent briefing (JSON fence) with task_context_index + dispatch snapshot"`
- 在 `WORKFLOW.md` 或 CLAUDE.md 的"Main Entry"章节加一句决策指引：
  > `harness next`：用于 review 阶段间流转（plan_review / ready_for_execution 等），只推进
  > `harness next --execute`：用于进入 executing / testing / acceptance 等实际派 subagent 工作的阶段，附 briefing

# 验收

- `harness next --help` 新文案到位
- `WORKFLOW.md` 或等效入口文档 有决策指引
- 契约 7 零新增违规
