# 工具：harness-export-feedback

**类型：** 自定义脚本
**状态：** active

## 用途

从 `.harness/feedback.jsonl` 导出反馈汇总，生成 `harness-feedback.json` 文件。

## 适用场景

- 导出反馈汇总
- 分析阶段跳过和持续时间
- 统计回归和 MCP 采用情况

## 调用方式

```bash
python tools/harness_export_feedback.py [--root <path>] [--reset]
```

## 参数

- `--root`: 仓库根目录（默认当前目录）
- `--reset`: 导出后清空反馈日志

## 返回值

- 0: 导出成功

## 示例

```bash
python tools/harness_export_feedback.py
python tools/harness_export_feedback.py --reset
python tools/harness_export_feedback.py --root /path/to/repo
```

## 输出格式

生成 `harness-feedback.json`，包含：
- `generated_at`: 生成时间
- `project_hash`: 项目哈希
- `period`: 反馈时间范围
- `summary`: 汇总统计
  - `stage_skips`: 阶段跳过统计
  - `stage_durations_avg_seconds`: 平均阶段持续时间
  - `regressions_created`: 创建的回归数
  - `mcp_adoptions`: MCP 采用情况
- `events_total`: 事件总数

## 注意事项

- 需要 `pyyaml` 依赖
- 输出文件覆盖已有文件

## 迭代记录
