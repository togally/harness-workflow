# 工具：harness-tool-search

**类型：** 自定义脚本
**状态：** active

## 用途

在本地工具索引中搜索匹配的工具。读取 `.workflow/tools/index/keywords.yaml` 并计算关键词重叠数，返回评分最高的工具。

## 适用场景

- 需要查找可用工具时
- 工具选择决策时
- 查询特定功能工具时

## 调用方式

```bash
python tools/harness_tool_search.py <keyword> [<keyword>...] [--root <path>]
```

## 参数

- `keywords`: 搜索关键词（至少一个）
- `--root`: 仓库根目录（默认当前目录）

## 返回值

- 0: 找到匹配工具
- 1: 未找到匹配或错误

## 示例

```bash
python tools/harness_tool_search.py edit write file
python tools/harness_tool_search.py git commit --root /path/to/repo
```

## 注意事项

- 关键词不区分大小写
- 评分相同情况下随机选择

## 迭代记录
