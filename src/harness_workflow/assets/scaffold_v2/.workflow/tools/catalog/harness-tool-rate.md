# 工具：harness-tool-rate

**类型：** 自定义脚本
**状态：** active

## 用途

为工具评分并更新累计平均值。评分存储在 `.workflow/tools/ratings.yaml` 中。

## 适用场景

- 使用工具后进行评分
- 工具迭代改进
- 工具质量跟踪

## 调用方式

```bash
python tools/harness_tool_rate.py <tool_id> <rating> [--root <path>]
```

## 参数

- `tool_id`: 工具 ID
- `rating`: 评分（1-5）
- `--root`: 仓库根目录（默认当前目录）

## 返回值

- 0: 评分成功
- 1: 评分无效或错误

## 示例

```bash
python tools/harness_tool_rate.py edit 5
python tools/harness_tool_rate.py bash 4 --root /path/to/repo
```

## 注意事项

- 评分必须在 1-5 范围内
- 新评分 = (旧评分 * 旧次数 + 新评分) / 新次数

## 迭代记录
