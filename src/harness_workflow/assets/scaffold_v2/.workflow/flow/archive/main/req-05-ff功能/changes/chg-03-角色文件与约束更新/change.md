# Change: chg-03

## Title

角色文件与约束更新

## Goal

在主 agent 和阶段角色文件中补充 ff 模式下的特殊职责和约束，并在约束文件中定义平台错误恢复和 skill 缺失处理路径。

## Scope

**包含**：
- `WORKFLOW.md`：补充主 agent 在 ff 模式下的协调职责
- `stages.md`：补充 ff 命令定义（与 chg-01 协调）
- 各阶段角色文件：在"退出条件"中增加"ff 模式下由 AI 自主确认"的说明
- `constraints/boundaries.md`：增加 ff 模式下 AI 自主决策的边界规则
- `constraints/recovery.md`：新增"平台级错误/会话损坏"和"skill 缺失"两类情况的恢复路径

**不包含**：
- 重写角色文件的核心职责
- 修改约束文件中的非 ff 相关内容

## Acceptance Criteria

- [ ] `WORKFLOW.md` 中主 agent 职责包含 ff 模式特殊规则
- [ ] 至少 `planning.md`、`executing.md`、`testing.md`、`acceptance.md` 已检查并补充 ff 说明（如需要）
- [ ] `constraints/boundaries.md` 中新增 ff 决策边界条目
- [ ] `constraints/recovery.md` 中新增"平台级错误/会话损坏"恢复条目
- [ ] `constraints/recovery.md` 中新增"skill 缺失"处理条目（包含搜索、安装替代方案或寻找等效工具的流程）
