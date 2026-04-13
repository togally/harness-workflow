# Harness Skill

## 概述
Harness 是工作流控制技能。主 agent 通过 harness 命令管理需求生命周期，节点任务由 subagent 执行。

## 使用前必读
执行任何 harness 命令前，必须先读 `workflow/state/runtime.yaml` 确认当前状态。

## 命令索引

| 命令 | 文件 | 说明 |
|------|------|------|
| `harness requirement` | `commands/requirement.md` | 创建需求 |
| `harness change` | `commands/change.md` | 创建变更 |
| `harness plan` | `commands/plan.md` | 创建变更计划 |
| `harness next` | `commands/next.md` | 推进 stage |
| `harness ff` | `commands/ff.md` | 快进到执行确认门 |
| `harness enter` | `commands/enter.md` | 进入 harness 对话锁定模式 |
| `harness exit` | `commands/exit.md` | 退出 harness 对话锁定模式 |
| `harness use` | `commands/use.md` | 切换当前活跃需求 |
| `harness status` | `commands/status.md` | 查看当前工作流状态 |
| `harness archive` | `commands/archive.md` | 归档已完成需求 |
| `harness regression` | `commands/regression.md` | 进入/控制 regression 流程 |
| `harness rename` | `commands/rename.md` | 重命名需求或变更 |

## 会话锁定规则
- 执行任何 harness 命令后（除 status、exit）自动进入 `conversation_mode: harness`
- 锁定期间只能在当前 requirement + stage 范围内工作
- `harness exit` 解除锁定

## 仓库检查
运行 `python3 tools/lint_harness_repo.py` 检查仓库结构合规性。
