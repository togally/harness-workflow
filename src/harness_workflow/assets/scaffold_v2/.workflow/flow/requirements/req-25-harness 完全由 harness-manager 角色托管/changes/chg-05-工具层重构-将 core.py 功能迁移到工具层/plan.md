# Change Plan

## 1. Development Steps

1. [x] 分析 `core.py` 中的所有函数，按功能分类
2. [x] 识别适合迁移到工具层的功能（需要 Python 高效执行的操作）
3. [x] 将选定功能实现为独立工具脚本：
   - tools/harness_tool_search.py
   - tools/harness_tool_rate.py
   - tools/harness_log_action.py
   - tools/harness_export_feedback.py
   - tools/harness_cycle_detector.py
4. [x] 在工具层注册工具（创建工具目录和 index）
   - 在 keywords.yaml 中注册工具关键词
   - 创建 catalog 文档
5. [x] 更新 cli.py 使用工具脚本
6. [x] 删除 core.py 中已迁移的逻辑
7. [x] 验证所有 harness 命令仍能正常工作

## 2. Verification Steps

- [x] `core.py` 中只保留 CLI 入口和最小化代码
- [x] 所有迁移的工具能正常被 toolsManager 识别
- [x] Agent 能通过 toolsManager 调用工具
- [x] 所有 harness 命令功能正常

## 3. 已迁移函数

| 原 core.py 函数 | 工具脚本 | 状态 |
|----------------|---------|------|
| search_tools | tools/harness_tool_search.py | 已迁移 |
| rate_tool | tools/harness_tool_rate.py | 已迁移 |
| log_action | tools/harness_log_action.py | 已迁移 |
| export_feedback | tools/harness_export_feedback.py | 已迁移 |
| Cycle detection 相关 | tools/harness_cycle_detector.py | 已迁移 |

## 4. 验证结果

```bash
# 工具搜索
$ harness tool-search edit write
Matched: edit
Catalog: catalog/edit.md
Description: 编辑或创建文件内容（Edit / Write）
Score: 5.0
Overlap: 2

# 工具评分
$ harness tool-rate edit 5
Rated edit: 5.0 (from 1 ratings)

# 反馈导出
$ harness feedback
Feedback exported to harness-feedback.json

# 状态查询
$ harness status
current_requirement: req-25
stage: executing
conversation_mode: open
```
