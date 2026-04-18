# Session Memory

## 1. Current Goal

- 完成 chg-05：工具层重构 - 将 core.py 功能迁移到工具层

## 2. Current Status

- [x] 分析 core.py 中的函数，按功能分类
- [x] 创建工具脚本：
  - tools/harness_tool_search.py - 工具搜索
  - tools/harness_tool_rate.py - 工具评分
  - tools/harness_log_action.py - 操作日志记录
  - tools/harness_export_feedback.py - 反馈导出
  - tools/harness_cycle_detector.py - 循环检测
- [x] 在 keywords.yaml 中注册新工具
- [x] 创建 catalog 文档
- [x] 更新 cli.py 使用工具脚本
- [x] 从 core.py 删除已迁移的函数
- [ ] 验证所有 harness 命令正常工作

## 3. Validated Approaches

### 迁移的工具函数
- search_tools -> tools/harness_tool_search.py
- rate_tool -> tools/harness_tool_rate.py
- log_action -> tools/harness_log_action.py
- export_feedback -> tools/harness_export_feedback.py
- Cycle detection 相关 -> tools/harness_cycle_detector.py

### CLI 调用方式
- CLI 通过 subprocess 调用工具脚本
- 使用 sys.executable 确保使用正确的 Python 解释器

### 工具注册
- 在 .workflow/tools/index/keywords.yaml 中注册工具关键词
- 在 .workflow/tools/catalog/ 中创建工具描述文档

## 4. Failed Paths

无

## 5. Candidate Lessons

### 2026-04-18: 工具层迁移策略
- Symptom: 初始尝试删除所有 core.py 业务逻辑，但 CLI 仍然依赖这些函数
- Cause: CLI 命令需要核心业务逻辑函数
- Fix: 采用渐进式迁移策略 - 将工具函数迁移到独立脚本，保留 CLI 命令函数在 core.py

## 6. Next Steps

1. 检查是否需要迁移更多函数到工具层
2. 考虑 Cycle Detection 函数是否需要迁移
3. 更新相关文档

## 7. Open Questions

- Cycle Detection 函数是否应该完全迁移到工具脚本，还是保留在 core.py 作为 Python 模块？
- 是否需要迁移其他辅助函数（如 normalize_language, slugify 等）到工具层？
