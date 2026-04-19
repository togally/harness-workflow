# Change: chg-01

## Title

更新 done 阶段角色文件与主 agent 职责

## Goal

在 `done.md` 和 `WORKFLOW.md` 中明确主 agent 在 done 阶段有义务将改进建议自动转为 suggest 条目。

## Scope

**包含**：
- 更新 `context/roles/done.md`，增加"建议转 suggest"的检查项
- 更新 `WORKFLOW.md` 的 done 阶段行为说明

**不包含**：
- 修改代码逻辑

## Acceptance Criteria

- [ ] `done.md` 中包含"将改进建议写入 suggest 池"的检查项
- [ ] `WORKFLOW.md` 中主 agent 的 done 职责包含此要求
