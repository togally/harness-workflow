# 工具：Edit / Write

**类型：** 内置工具
**状态：** active

## 适用场景
- **Edit**：修改已存在文件的部分内容（精确替换）
- **Write**：创建新文件 或 完整重写文件

## 不适用场景
- 修改已有文件时优先用 Edit，不用 Write（避免覆盖未读内容）

## 推荐 prompt 模式

| 任务类型 | 选择 |
|---------|------|
| 修改文件中某一段 | Edit（old_string → new_string） |
| 新建文件 | Write |
| 文件内容完全重写 | Write（先 Read 确认） |

## 注意事项
- Edit 前必须先 Read 文件
- Edit 的 old_string 必须在文件中唯一，否则用更多上下文区分
- testing / acceptance / regression 阶段禁用

## 迭代记录
