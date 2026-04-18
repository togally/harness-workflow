# Plan: chg-02

## Steps

1. 读取 `core.py` 中 `workflow_next` 或相关函数，找到进入 done 阶段的逻辑
2. 设计 `extract_suggestions_from_done_report(root, req_id)`：
   - 定位 `state/sessions/{req-id}/done-report.md`
   - 读取文件内容
   - 解析 `## 改进建议` 区块
   - 提取 `> **建议**` 或列表项 `- ` 或 `1. ` 开头的建议文本
   - 过滤空行和过短的行
   - 对每条建议调用 `create_suggestion(root, content)`
3. 在合适的时机调用该函数：
   - 方案 A：`workflow_next` 中将 stage 推进到 done 后自动调用
   - 方案 B：由主 agent 根据 `done.md` 的要求手动调用
   - **选择方案 A**，确保自动化，不依赖主 agent 记忆
4. 测试：手动构造一个 done-report，调用函数验证 suggest 创建
5. 保存修改

## Artifacts

- 更新后的 `src/harness_workflow/core.py`

## Dependencies

- 依赖 chg-01 的职责定义
