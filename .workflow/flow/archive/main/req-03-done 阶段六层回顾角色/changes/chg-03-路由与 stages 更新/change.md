# Change

## 1. Title

路由与 stages 更新

## 2. Goal

更新路由表和阶段定义，明确 `done` 阶段由**主 agent** 执行（非 subagent），并引用 `done.md` 作为检查清单：
- `context/index.md` Step 2 路由表增加 `done → done.md` 条目，标注（主 agent 执行）
- `flow/stages.md` done 阶段定义细化，明确主 agent 执行，引用 `done.md` 作为检查清单内容

## 3. Requirement

- `req-03-done 阶段六层回顾角色`

## 4. Scope

**包含**：
- 编辑 `context/index.md` Step 2 路由表，增加 `done → done.md` 条目，并标注（主 agent 执行）
- 编辑 `flow/stages.md` done 阶段定义，细化说明主 agent 执行，引用 `done.md` 作为检查清单

**不包含**：
- 不修改 `WORKFLOW.md`（属于 chg-01）
- 不创建 `done.md` 文件（属于 chg-02）
- 不修改其他阶段定义（只更新 done 阶段）

## 5. Next

- Add `design.md`
- Add `plan.md`
- Regression input requests live in `regression/required-inputs.md`
