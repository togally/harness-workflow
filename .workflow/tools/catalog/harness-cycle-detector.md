# 工具：harness-cycle-detector

**类型：** 自定义脚本
**状态：** active

## 用途

检测 subagent 调用链中的循环依赖。当检测到循环时，记录到 action-log.md 和 cycle-logs/ 目录。

## 适用场景

- subagent 派发前检测循环
- 防止无限递归的 agent 调用
- 调用链审计

## 调用方式

```bash
python tools/harness_cycle_detector.py --add <agent_id> [--role <role>] [--task <task>] [--session-path <path>] [--parent-id <id>] [--root <path>]
python tools/harness_cycle_detector.py --snapshot [--root <path>]
python tools/harness_cycle_detector.py --clear [--root <path>]
```

## 参数

- `--add`: 添加 agent 到调用链并检测循环
- `--role`: agent 角色
- `--task`: 任务描述
- `--session-path`: agent session memory 路径
- `--parent-id`: 父 agent ID
- `--snapshot`: 获取当前调用链快照
- `--clear`: 清除调用链
- `--root`: 仓库根目录（默认当前目录）

## 返回值

- 0: 无循环，添加成功或快照获取成功
- 1: 检测到循环或错误

## 示例

```bash
# 添加 agent 到调用链
python tools/harness_cycle_detector.py \
  --add "agent-123" \
  --role "executing" \
  --task "实现功能X" \
  --session-path ".workflow/state/sessions/agent-123.md"

# 获取调用链快照
python tools/harness_cycle_detector.py --snapshot

# 清除调用链
python tools/harness_cycle_detector.py --clear
```

## 检测逻辑

1. 检查 agent_id 是否已在调用链中
2. 如果存在，返回循环路径
3. 如果不存在，添加到调用链

## 输出

检测到循环时：
- 打印循环路径
- 写入 action-log.md
- 写入 cycle-logs/cycle-{timestamp}.md

## 迭代记录
