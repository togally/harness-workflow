# Requirement

## 1. Title

done 阶段六层回顾角色

## 2. Goal

当前 `done` 阶段是空白的——没有角色文件、没有结构化行为、没有六层视角回顾，结束只是状态字段变成 `done`。

本需求的目标：为 `done` 阶段增加一个**结构化回顾角色**，让流程结束时有明确的六层架构复盘动作，而不是靠人工记忆来决定"结束后该做什么"。

具体能力：
- 检查六层（context/tools/flow/state/evaluation/constraints）各层是否健康
- 工具层：本轮有无 CLI 工具、MCP 工具可以更好地服务某一层
- 流程层：是否完整走了正规阶段流程，有无短路
- 经验层：本轮经验是否已沉淀到 experience/ 文件
- 输出一份结构化的回顾报告，供归档前参考

## 3. Scope

**包含**：
- `WORKFLOW.md` 增加 `## done 阶段行为` 区块，定义主 agent 在 stage=done 时的六层回顾动作
- `done` 检查清单文件（`.workflow/context/roles/done.md`）作为**内容文件**（主 agent 按需读取），非 subagent briefing
- `context/index.md` 路由表补充 done 条目（标注由主 agent 执行）
- `flow/stages.md` 中 done 阶段定义细化（明确主 agent 执行，引用 done.md 作为检查清单）

**不包含**：
- 修改其他阶段（requirement_review / planning / executing / testing / acceptance）的角色
- 自动修复机制（回顾只是发现问题，修复走新 requirement 或 regression）
- CLI 命令变更（不新增 harness 子命令）

## 4. Acceptance Criteria

- `WORKFLOW.md` 包含 `## done 阶段行为` 区块，定义主 agent 的六层回顾动作
- `done` 检查清单文件 `context/roles/done.md` 存在，包含六层检查清单（逐层 checklist）、工具层适配性建议模板、经验沉淀验证步骤
- `context/index.md` Step 2 路由表包含 `done → done.md` 条目，并标注（主 agent 执行）
- `flow/stages.md` done 阶段定义明确主 agent 执行，引用 `done.md` 作为检查清单内容

## 5. Split Rules

### chg-01 WORKFLOW.md done 阶段行为

在 `WORKFLOW.md` 增加 `## done 阶段行为` 区块，定义主 agent 在 stage=done 时的动作：
- 读取 `context/roles/done.md`（作为检查清单）
- 逐层执行六层回顾检查（context/tools/flow/state/evaluation/constraints）
- 工具层专项：询问本轮有无 CLI/MCP 工具适配性问题
- 经验沉淀验证：确认 experience/ 文件已更新本轮教训
- 流程完整性检查：各阶段是否实际执行（非跳过）
- 输出回顾报告到 `session-memory.md` 或单独文件

### chg-02 done 检查清单文件

创建 `.workflow/context/roles/done.md` 作为**内容文件**（非 subagent briefing）：
- 六层检查清单（逐层 checklist）
- 工具层适配性问题模板（CLI/MCP 检查点）
- 经验沉淀验证步骤
- 流程完整性检查项
- 输出规范建议

### chg-03 路由与 stages 更新

- `context/index.md` Step 2 路由表增加 `done → done.md`，标注（主 agent 执行）
- `flow/stages.md` done 阶段定义细化，明确主 agent 执行，引用 `done.md` 作为检查清单
