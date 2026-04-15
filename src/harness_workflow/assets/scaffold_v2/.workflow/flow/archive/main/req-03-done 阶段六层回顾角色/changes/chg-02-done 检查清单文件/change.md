# Change

## 1. Title

done 检查清单文件

## 2. Goal

创建 `.workflow/context/roles/done.md` 作为**检查清单内容文件**（非 subagent briefing），供主 agent 在 done 阶段读取使用。文件包含：
- 六层检查清单（逐层 checklist：context/tools/flow/state/evaluation/constraints）
- 工具层适配性问题模板（CLI/MCP 检查点）
- 经验沉淀验证步骤
- 流程完整性检查项
- 输出规范建议

## 3. Requirement

- `req-03-done 阶段六层回顾角色`

## 4. Scope

**包含**：
- 创建 `.workflow/context/roles/done.md` 文件
- 文件内容：六层检查清单、工具层适配性问题模板、经验沉淀验证步骤、流程完整性检查项、输出规范建议
- 文件定位：作为**内容文件**（供主 agent 读取），非 subagent briefing

**不包含**：
- 不修改 `WORKFLOW.md`（属于 chg-01）
- 不更新 `context/index.md` 路由表（属于 chg-03）
- 不更新 `flow/stages.md`（属于 chg-03）
- 不为 `done` 阶段创建 subagent 角色文件（本文件是内容文件，非角色约束）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`
