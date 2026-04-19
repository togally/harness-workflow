# Requirement

## 1. Title

done 阶段建议自动转 suggest

## 2. Goal

当前 done 阶段会产出 `done-report.md`，其中包含"改进建议"段落。但这些建议如果未被用户立即行动，很容易随着需求归档而被遗忘。

本需求的目标是：**在 done 阶段结束时，自动将 `done-report.md` 中的改进建议提取为 `suggest` 条目**，写入 `.workflow/flow/suggestions/`，使用户后续可以随时通过 `harness suggest --apply` 将其转化为正式需求并进入工作流。

## 3. Scope

**包含**：
- 更新 `done.md`（done 阶段检查清单），增加"建议自动转 suggest"的明确要求
- 在 `core.py` 中实现自动解析 `done-report.md` 并提取建议的函数
- 为每条建议自动调用 `create_suggestion`，生成 `sug-NN-xxx.md`
- 更新 `WORKFLOW.md` 中主 agent 的 done 阶段职责说明
- 验证和文档更新

**不包含**：
- 修改现有 suggest 命令的接口
- 修改 stage 流转规则
- 开发 Web UI

## 4. Acceptance Criteria

- [ ] `done.md` 中包含"将改进建议写入 suggest 池"的检查项
- [ ] `core.py` 中实现了从 `done-report.md` 提取建议并自动创建 suggest 的函数
- [ ] 在一个完整需求走完后，`.workflow/flow/suggestions/` 下能自动出现对应的 suggest 文件
- [ ] 文档已更新

## 5. Split Rules

### chg-01 更新 done 阶段角色文件与主 agent 职责

- 在 `done.md` 的"完成前必须检查"或"输出规范建议"中增加：主 agent 应将 `done-report.md` 中的改进建议提取为 suggest
- 在 `WORKFLOW.md` 的 done 阶段行为中补充此职责

### chg-02 实现建议自动提取与 suggest 创建

在 `core.py` 中新增函数：
- `extract_suggestions_from_done_report(root, req_id)`：读取 `state/sessions/{req-id}/done-report.md`，解析 `## 改进建议` 或 `> **建议` 块，提取建议文本
- 对每条建议调用 `create_suggestion(root, content, title=None)`
- 输出创建结果

触发时机：
- 主 agent 在 done 阶段完成六层回顾并保存 `done-report.md` 后调用

### chg-03 验证与文档

- 用一个示例需求走完 done 阶段，验证 suggest 自动创建
- 更新 `stages.md` 或 `README.md`（如有必要）
- 重新打包安装
