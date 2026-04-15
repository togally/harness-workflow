# Harness Workflow

> 核心工作流规则见 [WORKFLOW.md](WORKFLOW.md)

## Hard Gate

未读取 `WORKFLOW.md`、`.workflow/context/index.md`、`.workflow/state/runtime.yaml` 前，立即停止，不执行任何动作。

如果这三个文件任一缺失、冲突或无法解析，立即停止，不允许回退旧入口。

## 平台特定说明

Claude Code 用户可通过 Skill 工具调用 Harness 工作流相关命令。
