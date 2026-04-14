# 工具：Grep / Glob

**类型：** 内置工具
**状态：** active

## 适用场景
- **Grep**：在文件内容中搜索特定字符串或模式
- **Glob**：按文件名模式查找文件路径

## 不适用场景
- 已知文件路径时直接用 Read
- 需要执行复杂 shell 逻辑时用 Bash

## 推荐 prompt 模式

| 任务类型 | 选择 |
|---------|------|
| 找包含某字符串的文件 | Grep（output_mode: files_with_matches） |
| 找某函数/变量定义 | Grep（pattern 用正则） |
| 找某类型文件 | Glob（pattern: **/*.md） |
| 查看匹配行的上下文 | Grep（output_mode: content，加 -C 参数） |

## 注意事项
- Grep 结果默认限制 250 行，大结果集用 head_limit 控制
- 优先使用 Grep/Glob 而非 Bash grep/find

## 迭代记录
