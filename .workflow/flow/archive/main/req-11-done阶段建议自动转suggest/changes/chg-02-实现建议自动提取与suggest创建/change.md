# Change: chg-02

## Title

实现建议自动提取与 suggest 创建

## Goal

在 `core.py` 中实现从 `done-report.md` 提取改进建议并自动创建 suggest 文件的函数。

## Scope

**包含**：
- 新增 `extract_suggestions_from_done_report(root, req_id)` 函数
- 解析 `state/sessions/{req-id}/done-report.md` 中的建议段落
- 对每条建议调用 `create_suggestion`
- 在 `harness next` 进入 done 阶段或 done 阶段结束时触发

**不包含**：
- 修改 suggest 命令本身
- 修改 done-report 的格式要求

## Acceptance Criteria

- [ ] `core.py` 中存在提取并创建 suggest 的函数
- [ ] 函数能正确解析常见的建议格式（`> **建议` 或 `## 改进建议` 下的列表）
- [ ] 有明确的创建结果输出
