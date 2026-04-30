# Harness Workflow

> 核心工作流规则见 [WORKFLOW.md](WORKFLOW.md)

## Hard Gate

未读取 `WORKFLOW.md`、`.workflow/context/index.md`、`.workflow/state/runtime.yaml` 前，立即停止，不执行任何动作。

如果这三个文件任一缺失、冲突或无法解析，立即停止，不允许回退旧入口。

## 平台特定说明

Claude Code 用户可通过 Skill 工具调用 Harness 工作流相关命令。

## 项目路书

任务入场即读路书，AI 用作项目地图与代码导航，避免全局盲扫代码。项目知识与代码导航在 `artifacts/project/playbooks/`：

- `artifacts/project/playbooks/overview.md`（项目概述：定位、术语、里程碑）
- `artifacts/project/playbooks/architecture.md`（架构地图：技术栈、目录职责、数据流）
- `artifacts/project/playbooks/runbook.md`（运行手册：启动/测试/构建命令、环境变量）
- `artifacts/project/playbooks/code-map.md`（代码导航：关键词 → 领域索引，agent 入口）
