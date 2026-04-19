# 工具：harness-log-action

**类型：** 自定义脚本
**状态：** active

## 用途

将操作记录追加到 `.workflow/state/action-log.md`。

## 适用场景

- 记录操作日志
- 审计操作历史
- 追踪工具使用

## 调用方式

```bash
python tools/harness_log_action.py --operation <name> --description <desc> --result <result> [--tool-id <id>] [--rating <n>] [--root <path>]
```

## 参数

- `--operation`: 操作名称（必需）
- `--description`: 操作描述（必需）
- `--result`: 操作结果（必需）
- `--tool-id`: 使用的工具 ID（可选）
- `--rating`: 工具评分 1-5（可选）
- `--root`: 仓库根目录（默认当前目录）

## 返回值

- 0: 记录成功
- 1: 错误

## 示例

```bash
python tools/harness_log_action.py \
  --operation "create-requirement" \
  --description "创建需求 req-26" \
  --result "成功" \
  --tool-id "edit" \
  --rating 5
```

## 注意事项

- 日志文件不存在时会自动创建
- 目录不存在时会自动创建

## 迭代记录
