# Change

## 1. Title

WORKFLOW.md done 阶段行为

## 2. Goal

在 `WORKFLOW.md` 中增加 `## done 阶段行为` 区块，定义主 agent 在 stage=done 时的六层回顾动作，包括：
- 读取 `context/roles/done.md` 作为检查清单
- 逐层执行六层回顾检查（context/tools/flow/state/evaluation/constraints）
- 工具层适配性问题询问（CLI/MCP 检查）
- 经验沉淀验证
- 流程完整性检查
- 输出回顾报告到 session-memory.md

## 3. Requirement

- `req-03-done 阶段六层回顾角色`

## 4. Scope

**包含**：
- 编辑 `WORKFLOW.md` 文件，在适当位置（例如 `## 职责外问题处理` 之后）新增 `## done 阶段行为` 区块
- 区块内容定义主 agent 在 stage=done 时的动作流程
- 引用 `context/roles/done.md` 作为检查清单来源

**不包含**：
- 不修改其他角色文件
- 不修改 `context/index.md`（属于 chg-03）
- 不创建 `done.md` 检查清单文件（属于 chg-02）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`
